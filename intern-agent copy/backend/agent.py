import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# GLM API配置
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4")


def call_glm(prompt: str, temperature: float = 0.7) -> str:
    """调用智谱AI API"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"]


def generate_summary(log_data: dict) -> str:
    """使用GLM生成每日学习摘要"""
    prompt = f"""你是一个学习记录助手。请根据以下学习记录生成一份简洁的每日摘要：

今日任务：
{json.dumps(log_data.get('tasks', []), ensure_ascii=False, indent=2)}

今日学习：
{json.dumps(log_data.get('learnings', []), ensure_ascii=False, indent=2)}

请用中文生成一段简短的摘要（100字以内），概括今天的主要收获和学习重点。"""
    return call_glm(prompt)


def suggest_tags(log_data: dict) -> list:
    """使用GLM智能推荐标签"""
    prompt = f"""根据以下学习内容，推荐合适的标签（最多5个）：

学习内容：
{json.dumps(log_data.get('learnings', []), ensure_ascii=False, indent=2)}

标签分类：技术、业务、工具、软技能

请直接返回JSON数组格式的标签列表，例如：["Python", "API设计", "团队协作"]
只返回标签列表，不要其他内容。"""
    try:
        response = call_glm(prompt)
        tags = json.loads(response)
        return tags if isinstance(tags, list) else []
    except:
        return []


def recognize_image(base64_image: str) -> str:
    """使用GLM-4V直接解释图片内容"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
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
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"]


def answer_question(question: str, knowledge_context: str) -> str:
    """基于知识库回答问题"""
    prompt = f"""你是一个学习知识库助手。请根据以下知识库内容回答用户的问题。

知识库内容：
{knowledge_context}

用户问题：{question}

请用中文回答，如果知识库中没有相关信息，请说明。"""
    return call_glm(prompt)


def create_learning_agent():
    """创建学习记录Agent（LangChain风格）"""
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    from langchain.tools import Tool
    from langchain import hub

    # 使用OpenAI兼容接口调用GLM
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
    return AgentExecutor(agent=agent, tools=tools, verbose=True)