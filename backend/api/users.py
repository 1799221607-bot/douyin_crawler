from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from db.repository import UserRepo
from api.auth import get_current_user
from utils.security import get_password_hash

router = APIRouter(prefix="/api/users", tags=["用户管理"])

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """用户列表（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看用户列表")
    
    repo = UserRepo(db)
    users = await repo.list_all()
    # 隐藏哈希密码
    return {"data": [
        {
            "id": u.id, 
            "username": u.username, 
            "role": u.role, 
            "is_active": u.is_active,
            "created_at": u.created_at
        } for u in users
    ]}

@router.post("")
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建新用户（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权创建用户")
    
    repo = UserRepo(db)
    # 检查重名
    existing = await repo.get_by_username(body.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    new_user = await repo.create(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        role=body.role
    )
    await db.commit()
    return {"message": "用户创建成功", "id": new_user.id}

@router.put("/password")
async def update_password(
    body: PasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """修改自己的密码"""
    from utils.security import verify_password
    
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    repo = UserRepo(db)
    await repo.update(current_user.id, hashed_password=get_password_hash(body.new_password))
    await db.commit()
    return {"message": "密码修改成功"}

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除用户（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除用户")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    repo = UserRepo(db)
    await repo.delete(user_id)
    await db.commit()
    return {"message": "用户已删除"}
