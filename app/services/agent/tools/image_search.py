import base64
from typing import Dict, Any, List
from langchain.tools import BaseTool
import logging

from app.services.taobao import taobao_api

logger = logging.getLogger(__name__)


class ImageSearchTool(BaseTool):
    """用于通过图片搜索淘宝商品的工具"""
    
    name: str = "image_search"
    description: str = "通过上传的图片搜索相似的淘宝商品"
    
    def _run(self, image_data: str) -> List[Dict[str, Any]]:
        """执行图片搜索
        
        Args:
            image_data: Base64编码的图片数据
        """
        logger.info("🖼️ ImageSearchTool 开始执行图片搜索")
        logger.info(f"📊 图片数据长度: {len(image_data)} 字符")
        
        # 验证图片数据
        try:
            logger.info("🔍 验证图片数据格式...")
            
            # 如果图片数据包含base64前缀，则去除
            if "," in image_data:
                logger.info("🔄 移除base64前缀...")
                image_data = image_data.split(",", 1)[1]
                logger.info(f"📊 处理后图片数据长度: {len(image_data)} 字符")
            
            # 尝试解码以验证是否为有效的base64
            logger.info("🔄 验证base64编码...")
            decoded_data = base64.b64decode(image_data)
            logger.info(f"✅ 图片数据验证成功，解码后大小: {len(decoded_data)} 字节")
            
        except Exception as e:
            logger.error("❌ 图片数据验证失败")
            logger.error(f"🚨 错误详情: {str(e)}")
            return [{"error": f"无效的图片数据: {str(e)}"} ]
        
        try:
            # 调用淘宝API进行图片搜索
            logger.info("🔄 调用淘宝API进行图片搜索...")
            products = taobao_api.search_by_image(image_data)
            logger.info(f"✅ API调用成功，返回 {len(products)} 个商品")
            
            # 转换为字典列表
            logger.info("🔄 格式化商品数据...")
            formatted_products = [self._format_product(product) for product in products]
            logger.info(f"✅ 商品数据格式化完成，共 {len(formatted_products)} 个商品")
            
            # 记录前几个商品的基本信息
            for i, product in enumerate(formatted_products[:3]):
                similarity = product.get('similarity', '未知')
                logger.info(f"📦 商品 {i+1}: {product.get('title', '无标题')[:50]}... - 相似度: {similarity}")
            
            return formatted_products
            
        except Exception as e:
            logger.error("❌ ImageSearchTool 执行失败")
            logger.error(f"🚨 错误详情: {str(e)}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            return [{"error": f"图片搜索失败: {str(e)}"}]
    
    def _format_product(self, product) -> Dict[str, Any]:
        """格式化商品信息"""
        logger.debug(f"🔄 格式化图片搜索商品: {product.item_id}")
        
        formatted = {
            "item_id": product.item_id,
            "title": product.title,
            "price": product.price,
            "original_price": product.original_price,
            "image_url": product.image_url,
            "detail_url": product.detail_url,
            "shop_name": product.shop_name,
            "similarity": product.metadata.get("similarity", "未知") if product.metadata else "未知",
            "category": product.category,
        }
        
        logger.debug(f"✅ 图片搜索商品格式化完成: {formatted['title'][:30]}... - 相似度: {formatted['similarity']}")
        return formatted