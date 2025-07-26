from typing import Dict, Any, List
from langchain.tools import BaseTool

from app.services.taobao import taobao_api
from app.schemas.chat import ProductBase


class ProductSearchTool(BaseTool):
    """用于搜索淘宝商品的工具"""
    
    name: str = "product_search"
    description: str = "搜索淘宝商品，可以根据关键词查找相关商品信息"
    
    def _run(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """执行商品搜索"""
        # 获取可选参数
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 10)
        
        # 调用淘宝API搜索商品
        products = taobao_api.search_material(query, page_no=page, page_size=page_size)
        
        # 转换为字典列表
        return [self._format_product(product) for product in products]
    
    def _format_product(self, product: ProductBase) -> Dict[str, Any]:
        """格式化商品信息"""
        return {
            "item_id": product.item_id,
            "title": product.title,
            "price": product.price,
            "original_price": product.original_price,
            "discount": self._calculate_discount(product.price, product.original_price),
            "image_url": product.image_url,
            "detail_url": product.detail_url,
            "shop_name": product.shop_name,
            "sales": product.sales,
            "rating": product.rating,
            "category": product.category,
        }
    
    def _calculate_discount(self, current_price: str, original_price: str) -> str:
        """计算折扣"""
        if not original_price or not current_price:
            return "无折扣信息"
        
        try:
            current = float(current_price)
            original = float(original_price)
            if original <= 0:
                return "无折扣信息"
            
            discount = current / original * 10
            return f"{discount:.1f}折"
        except (ValueError, TypeError):
            return "无折扣信息"


class ProductDetailTool(BaseTool):
    """用于获取淘宝商品详情的工具"""
    
    name: str = "product_detail"
    description: str = "获取淘宝商品的详细信息，包括价格、描述、评分等"
    
    def _run(self, item_id: str) -> Dict[str, Any]:
        """获取商品详情"""
        # 调用淘宝API获取商品详情
        product = taobao_api.get_product_details(item_id)
        
        if not product:
            return {"error": "未找到商品信息"}
        
        # 转换为字典
        return {
            "item_id": product.item_id,
            "title": product.title,
            "price": product.price,
            "original_price": product.original_price,
            "description": product.description,
            "image_url": product.image_url,
            "detail_url": product.detail_url,
            "shop_name": product.shop_name,
            "sales": product.sales,
            "rating": product.rating,
            "category": product.category,
            "metadata": product.metadata,
        }