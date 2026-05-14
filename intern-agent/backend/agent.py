"""
AI Agent 模块

提供基于 GLM API 的智能功能：
- 学习摘要生成
- 标签推荐
- 图片识别
"""

import json
import logging
import os
from typing import List, Optional

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout

load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# GLM API 配置
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4")
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_TIMEOUT = int(os.getenv("GLM_TIMEOUT", "30"))  # API 超时时间（秒）

if not GLM_API_KEY:
    logger.warning("未配置 GLM_API_KEY，AI 功能将不可用")


def call_glm(prompt: str, temperature: float = 0.7, max_retries: int = 3) -> str:
    """
    调用智谱 AI API
    
    Args:
        prompt: 提示词
        temperature: 温度参数（0-1），控制输出的随机性
        max_retries: 最大重试次数
        
    Returns:
        API 返回的文本内容
        
    Raises:
        ValueError: API Key 未配置
        RequestException: API 调用失败
    """
    if not GLM_API_KEY:
        raise ValueError("GLM_API_KEY 未配置，请检查环境变量")
    
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": GLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    
    # 重试机制
    for attempt in range(max_retries):
        try:
            logger.info(f"调用 GLM API (尝试 {attempt + 1}/{max_retries})")
            
            response = requests.post(
                GLM_API_URL,
                headers=headers,
                json=data,
                timeout=GLM_TIMEOUT
            )
            
            # 检查 HTTP 状态码
            response.raise_for_status()
            
            result = response.json()
            
            # 检查 API 返回格式
            if "choices" not in result or len(result["choices"]) == 0:
                raise ValueError("API 返回格式异常：缺少 choices 字段")
            
            content = result["choices"][0]["message"]["content"]
            logger.info("GLM API 调用成功")
            return content
            
        except Timeout:
            logger.warning(f"GLM API 超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise RequestException(f"API 调用超时，已重试 {max_retries} 次")
                
        except requests.HTTPError as e:
            logger.error(f"GLM API HTTP 错误: {e}")
            if e.response.status_code == 401:
                raise ValueError("API Key 无效或已过期")
            elif e.response.status_code == 429:
                logger.warning("API 请求频率限制，等待重试...")
                import time
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise RequestException(f"API 调用失败: HTTP {e.response.status_code}")
                
        except (KeyError, IndexError) as e:
            logger.error(f"API 返回数据格式错误: {e}")
            raise ValueError(f"API 返回数据格式错误: {e}")
            
        except Exception as e:
            logger.error(f"GLM API 调用异常: {e}")
            if attempt == max_retries - 1:
                raise RequestException(f"API 调用失败: {str(e)}")
    
    raise RequestException("API 调用失败，已达到最大重试次数")


def generate_summary(log_data: dict) -> Optional[str]:
    """
    使用 GLM 生成每日学习摘要
    
    Args:
        log_data: 学习记录数据字典
        
    Returns:
        生成的摘要文本，失败时返回 None
    """
    try:
        prompt = f"""你是一个学习记录助手。请根据以下学习记录生成一份简洁的每日摘要：

今日任务：
{json.dumps(log_data.get('tasks', []), ensure_ascii=False, indent=2)}

今日学习：
{json.dumps(log_data.get('learnings', []), ensure_ascii=False, indent=2)}

请用中文生成一段简短的摘要（100字以内），概括今天的主要收获和学习重点。"""
        
        summary = call_glm(prompt)
        logger.info("学习摘要生成成功")
        return summary
        
    except Exception as e:
        logger.error(f"生成学习摘要失败: {e}")
        return None


def suggest_tags(log_data: dict) -> List[str]:
    """
    使用 GLM 智能推荐标签
    
    Args:
        log_data: 学习记录数据字典
        
    Returns:
        推荐的标签列表，失败时返回空列表
    """
    try:
        prompt = f"""根据以下学习内容，推荐合适的标签（最多5个）：

学习内容：
{json.dumps(log_data.get('learnings', []), ensure_ascii=False, indent=2)}

标签分类：技术、业务、工具、软技能

请直接返回JSON数组格式的标签列表，例如：["Python", "API设计", "团队协作"]
只返回标签列表，不要其他内容。"""
        
        response = call_glm(prompt)
        
        # 尝试解析 JSON
        try:
            tags = json.loads(response)
            if isinstance(tags, list):
                # 验证标签格式
                valid_tags = [str(tag) for tag in tags if tag]
                logger.info(f"标签推荐成功: {valid_tags}")
                return valid_tags[:5]  # 最多返回 5 个标签
            else:
                logger.warning(f"API 返回的不是列表: {response}")
                return []
        except json.JSONDecodeError:
            logger.warning(f"无法解析标签 JSON: {response}")
            return []
            
    except Exception as e:
        logger.error(f"推荐标签失败: {e}")
        return []


def recognize_image(base64_image: str) -> str:
    """
    使用 GLM-4V 解释图片内容
    
    Args:
        base64_image: Base64 编码的图片数据
        
    Returns:
        图片内容的文字描述
        
    Raises:
        ValueError: 图片数据无效
        RequestException: API 调用失败
    """
    if not base64_image or len(base64_image) < 100:
        raise ValueError("图片数据无效或过小")
    
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "glm-4v",
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请直接介绍这张图片的内容，告诉用户这张图在展示什么。\n\n要求：\n1. 不要逐字转录图片中的文字，不要列出每一行每一列的原始内容\n2. 直接概括这张图的主题和结构，比如这张图是一个什么表格/列表/图表，包含几大类，每类是什么\n3. 用自然的中文描述关键信息，像给人讲解一样介绍内容\n4. 如果是表格，说明表格有几列、分别是什么维度、各行代表什么\n5. 不要添加多余的分析、评价、总结或建议，只描述图中实际展示的内容\n6. 如果图片是分类/分条的信息，请直接说有几类，分别是什么\n\n示例风格：\n这张图是一个XX表格/列表，包含X大类，分别是...其中...\n\n请直接输出内容描述，不要添加格式说明。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }]
    }
    
    try:
        logger.info("开始图片识别")
        
        response = requests.post(
            GLM_API_URL,
            headers=headers,
            json=data,
            timeout=GLM_TIMEOUT
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError("API 返回格式异常")
        
        content = result["choices"][0]["message"]["content"]
        logger.info("图片识别成功")
        return content
        
    except Timeout:
        logger.error("图片识别超时")
        raise RequestException("图片识别超时，请稍后重试")
        
    except requests.HTTPError as e:
        logger.error(f"图片识别 HTTP 错误: {e}")
        if e.response.status_code == 401:
            raise ValueError("API Key 无效或已过期")
        raise RequestException(f"图片识别失败: HTTP {e.response.status_code}")
        
    except Exception as e:
        logger.error(f"图片识别失败: {e}")
        raise RequestException(f"图片识别失败: {str(e)}")


def answer_question(question: str, knowledge_context: str) -> str:
    """
    基于知识库回答问题
    
    Args:
        question: 用户问题
        knowledge_context: 知识库上下文
        
    Returns:
        回答内容
    """
    try:
        prompt = f"""你是一个学习知识库助手。请根据以下知识库内容回答用户的问题。

知识库内容：
{knowledge_context}

用户问题：{question}

请用中文回答，如果知识库中没有相关信息，请说明。"""
        
        answer = call_glm(prompt)
        logger.info("问题回答成功")
        return answer
        
    except Exception as e:
        logger.error(f"回答问题失败: {e}")
        raise


def create_learning_agent():
    """
    创建学习记录 Agent（LangChain 风格）
    
    Returns:
        AgentExecutor 实例
    """
    try:
        from langchain.agents import AgentExecutor, create_openai_functions_agent
        from langchain_openai import ChatOpenAI
        from langchain.tools import Tool
        from langchain import hub

        # 使用 OpenAI 兼容接口调用 GLM
        llm = ChatOpenAI(
            model="glm-4",
            openai_api_key=GLM_API_KEY,
            openai_api_base="https://open.bigmodel.cn/api/paas/v4",
            temperature=0.7
        )

        tools = [
            Tool(name="GenerateSummary", func=generate_summary, description="生成每日学习摘要"),
            Tool(name="SuggestTags", func=suggest_tags, description="推荐合适的标签"),
            Tool(name="AnswerQuestion", func=answer_question, description="基于知识库回答问题")
        ]

        prompt = hub.pull("hwchase17/openai-functions-agent")
        agent = create_openai_functions_agent(llm, tools, prompt)
        
        logger.info("Learning Agent 创建成功")
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
        
    except ImportError as e:
        logger.error(f"LangChain 导入失败: {e}")
        raise ImportError("请安装 langchain 和 langchain-openai: pip install langchain langchain-openai")
    except Exception as e:
        logger.error(f"创建 Agent 失败: {e}")
        raise
