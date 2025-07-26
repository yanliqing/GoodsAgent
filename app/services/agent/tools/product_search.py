from typing import Dict, Any, List
from langchain.tools import BaseTool
import logging

from app.services.taobao import taobao_api
from app.schemas.chat import ProductBase

logger = logging.getLogger(__name__)


class ProductSearchTool(BaseTool):
    """用于搜索淘宝商品的工具"""
    
    name: str = "product_search"
    description: str = "搜索淘宝商品，可以根据关键词查找相关商品信息"
    
    def _run(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """执行商品搜索"""
        logger.info("🔍 ProductSearchTool 开始执行商品搜索")
        logger.info(f"📝 搜索关键词: {query}")
        logger.info(f"📊 额外参数: {kwargs}")
        
        # 获取可选参数
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 10)
        
        logger.info(f"📄 分页参数 - 页码: {page}, 每页数量: {page_size}")
        
        try:
            # 调用淘宝API搜索商品
            logger.info("🔄 调用淘宝API搜索商品...")
            products = taobao_api.search_material(query, page_no=page, page_size=page_size)
            logger.info(f"✅ API调用成功，返回 {len(products)} 个商品")
            
            # 转换为字典列表
            logger.info("🔄 格式化商品数据...")
            formatted_products = [self._format_product(product) for product in products]
            logger.info(f"✅ 商品数据格式化完成，共 {len(formatted_products)} 个商品")
            
            # 记录前几个商品的基本信息
            for i, product in enumerate(formatted_products[:3]):
                logger.info(f"📦 商品 {i+1}: {product.get('title', '无标题')[:50]}... - 价格: {product.get('price', '未知')}")
            
            return formatted_products
            
        except Exception as e:
            logger.error("❌ ProductSearchTool 执行失败")
            logger.error(f"🚨 错误详情: {str(e)}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            return []
    
    def _format_product(self, product: ProductBase) -> Dict[str, Any]:
        """格式化商品信息"""
        logger.debug(f"🔄 格式化商品: {product.item_id}")
        
        formatted = {
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
        
        logger.debug(f"✅ 商品格式化完成: {formatted['title'][:30]}...")
        return formatted
    
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
        logger.info("🔍 ProductDetailTool 开始获取商品详情")
        logger.info(f"🆔 商品ID: {item_id}")
        
        try:
            # 调用淘宝API获取商品详情
            logger.info("🔄 调用淘宝API获取商品详情...")
            product = taobao_api.get_product_details(item_id)
            
            if not product:
                logger.warning("⚠️ 未找到商品信息")
                return {"error": "未找到商品信息"}
            
            logger.info(f"✅ 成功获取商品详情: {product.title[:50]}...")
            
            # 转换为字典
            result = {
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
            
            logger.info(f"📦 商品详情: 标题={result['title'][:30]}..., 价格={result['price']}, 店铺={result['shop_name']}")
            return result
            
        except Exception as e:
            logger.error("❌ ProductDetailTool 执行失败")
            logger.error(f"🚨 错误详情: {str(e)}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            return {"error": f"获取商品详情失败: {str(e)}"}