import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

# API Key 配置
API_KEY = os.getenv("API_KEY", "")
if not API_KEY:
    # 如果没有配置 API_KEY，生成一个随机密钥（仅用于开发环境）
    API_KEY = secrets.token_urlsafe(32)
    print(f"⚠️  警告: 未配置 API_KEY，已生成临时密钥: {API_KEY}")
    print("请在生产环境中设置 API_KEY 环境变量")

security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    验证 API Key
    
    Args:
        credentials: HTTP Bearer 认证凭据
        
    Returns:
        验证通过的 API Key
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_optional_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[str]:
    """
    可选的 API Key 验证（用于某些公开端点）
    
    Args:
        credentials: HTTP Bearer 认证凭据（可选）
        
    Returns:
        验证通过的 API Key 或 None
    """
    if credentials and credentials.credentials == API_KEY:
        return credentials.credentials
    return None
