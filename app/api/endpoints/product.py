from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.chat import ProductQuery, ProductSearchResponse, ProductBase
from app.services.taobao import taobao_api

router = APIRouter()


@router.post("/search", response_model=ProductSearchResponse)
async def search_products(
    query: ProductQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """搜索商品
    
    Args:
        query: 搜索查询
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        搜索结果
    """
    # 调用淘宝API搜索商品
    products = taobao_api.search_material(
        query=query.query,
        page_no=query.page,
        page_size=query.page_size
    )
    
    # 返回结果
    return ProductSearchResponse(
        products=products,
        total=len(products),  # 实际应用中应从API获取总数
        page=query.page,
        page_size=query.page_size
    )


@router.get("/detail/{item_id}", response_model=ProductBase)
async def get_product_detail(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取商品详情
    
    Args:
        item_id: 商品ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        商品详情
    """
    # 调用淘宝API获取商品详情
    product = taobao_api.get_product_details(item_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    return product