from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from loguru import logger

from database import get_db
from db.repository import UserRepo, LoginLogRepo
from utils.security import verify_password, create_access_token, decode_access_token
from utils.ip_lookup import get_ip_location
from config import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/auth", tags=["认证管理"])
limiter = Limiter(key_func=get_remote_address)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    """依赖项：从 Token 中获取当前用户"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌信息错误")
    
    repo = UserRepo(db)
    user = await repo.get_by_username(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号已被禁用")
    
    return user

@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录接口"""
    user_repo = UserRepo(db)
    log_repo = LoginLogRepo(db)
    
    # 1. 查找用户
    user = await user_repo.get_by_username(form_data.username)
    
    # 获取客户端信息
    ip = request.client.host
    ua = request.headers.get("user-agent")
    location = await get_ip_location(ip)
    
    error_msg = None
    if not user:
        error_msg = "用户不存在"
    elif not verify_password(form_data.password, user.hashed_password):
        error_msg = "密码错误"
    elif not user.is_active:
        error_msg = "账号已被禁用"
        
    if error_msg:
        # 记录失败日志
        await log_repo.create(
            username=form_data.username,
            ip_address=ip,
            location=location,
            user_agent=ua,
            status="failed",
            error_msg=error_msg
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 登录成功
    access_token = create_access_token(data={"sub": user.username})
    
    # 3. 记录成功日志
    await log_repo.create(
        username=user.username,
        ip_address=ip,
        location=location,
        user_agent=ua,
        status="success"
    )
    await db.commit()
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }

@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    """获取个人信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

@router.get("/logs")
async def get_login_logs(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """查看登录日志（仅限管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    repo = LoginLogRepo(db)
    logs = await repo.list_latest(50)
    return {"data": logs}
