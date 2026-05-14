#!/usr/bin/env python3
"""
配置验证脚本

检查所有必要的配置项是否正确设置
"""

import os
import sys
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_config():
    """检查配置项"""
    print("=" * 60)
    print("配置验证")
    print("=" * 60)
    
    # 必需的配置项
    required_configs = {
        "DATABASE_URL": "数据库连接字符串",
        "API_KEY": "API 认证密钥",
        "GLM_API_KEY": "GLM API 密钥",
    }
    
    # 可选的配置项
    optional_configs = {
        "GLM_MODEL": "GLM 模型",
        "GLM_TIMEOUT": "API 超时时间",
        "DB_POOL_SIZE": "数据库连接池大小",
        "ALLOWED_ORIGINS": "CORS 允许的源",
        "HOST": "服务器地址",
        "PORT": "服务器端口",
    }
    
    errors = []
    warnings = []
    
    # 检查必需配置
    print("\n必需配置项:")
    for key, desc in required_configs.items():
        value = os.getenv(key)
        if not value:
            errors.append(f"❌ {key} ({desc}): 未设置")
            print(f"  ❌ {key}: 未设置")
        elif value.startswith("your-") or value == "password":
            warnings.append(f"⚠️  {key} ({desc}): 使用默认值，请修改")
            print(f"  ⚠️  {key}: 使用默认值")
        else:
            # 隐藏敏感信息
            if "KEY" in key or "PASSWORD" in key:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"  ✅ {key}: {display_value}")
    
    # 检查可选配置
    print("\n可选配置项:")
    for key, desc in optional_configs.items():
        value = os.getenv(key)
        if value:
            print(f"  ✅ {key}: {value}")
        else:
            print(f"  ⚪ {key}: 未设置（使用默认值）")
    
    # 检查数据库连接
    print("\n数据库连接测试:")
    try:
        from db import test_connection
        if test_connection():
            print("  ✅ 数据库连接成功")
        else:
            errors.append("❌ 数据库连接失败")
            print("  ❌ 数据库连接失败")
    except Exception as e:
        errors.append(f"❌ 数据库连接测试失败: {e}")
        print(f"  ❌ 数据库连接测试失败: {e}")
    
    # 检查 API Key 格式
    print("\nAPI Key 验证:")
    api_key = os.getenv("API_KEY", "")
    if len(api_key) < 20:
        warnings.append("⚠️  API_KEY 长度过短，建议使用更长的密钥")
        print(f"  ⚠️  API Key 长度: {len(api_key)} (建议至少 20 字符)")
    else:
        print(f"  ✅ API Key 长度: {len(api_key)}")
    
    # 检查 GLM API Key
    print("\nGLM API 验证:")
    glm_key = os.getenv("GLM_API_KEY", "")
    if not glm_key:
        errors.append("❌ GLM_API_KEY 未设置，AI 功能将不可用")
        print("  ❌ GLM API Key 未设置")
    else:
        print(f"  ✅ GLM API Key 已设置 (长度: {len(glm_key)})")
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个错误:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print(f"\n⚠️  发现 {len(warnings)} 个警告:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ 所有配置项验证通过！")
        return True
    elif not errors:
        print("\n✅ 必需配置项验证通过，但建议处理警告项")
        return True
    else:
        print("\n❌ 配置验证失败，请修复错误后重试")
        return False

if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)
