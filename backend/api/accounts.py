from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from db.repository import AccountRepo
from api.auth import get_current_user

router = APIRouter(prefix="/api/accounts", tags=["账号池管理"])

class AccountCreate(BaseModel):
    platform: str
    username: str
    cookie: str
    proxy_url: Optional[str] = None
    ua: Optional[str] = None

class AccountUpdate(BaseModel):
    username: Optional[str] = None
    cookie: Optional[str] = None
    proxy_url: Optional[str] = None
    ua: Optional[str] = None
    status: Optional[str] = None

@router.get("")
async def list_accounts(
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取账号列表"""
    repo = AccountRepo(db)
    if platform:
        accounts = await repo.list_by_platform(platform)
    else:
        # 简单起见，这里直接查询所有
        from db.models import PlatformAccount
        from sqlalchemy import select
        result = await db.execute(select(PlatformAccount))
        accounts = result.scalars().all()
    
    return {"data": accounts}

@router.post("")
async def create_account(
    body: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """添加新账号"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作账号池")
    
    repo = AccountRepo(db)
    new_account = await repo.create(**body.dict())
    await db.commit()
    return {"message": "账号已添加", "id": new_account.id}

@router.put("/{account_id}")
async def update_account(
    account_id: int,
    body: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新账号信息/Cookie"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作账号池")
    
    repo = AccountRepo(db)
    updated = await repo.update(account_id, **body.dict(exclude_unset=True))
    await db.commit()
    return {"message": "更新成功", "data": updated}

@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除账号"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作账号池")
    
    repo = AccountRepo(db)
    await repo.delete(account_id)
    await db.commit()
    return {"message": "账号已删除"}
