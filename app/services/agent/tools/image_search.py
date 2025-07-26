import base64
from typing import Dict, Any, List
from langchain.tools import BaseTool

from app.services.taobao import taobao_api


class ImageSearchTool(BaseTool):
    """用于通过图片搜索淘宝商品的工具"""
    
    name: str = "image_search"
    description: str = "通过上传的图片搜索相似的淘宝商品"
    
    def _run(self, image_data: str) -> List[Dict[str, Any]]:
        """执行图片搜索
        
        Args:
            image_data: Base64编码的图片数据
        """
        # 验证图片数据
        try:
            # 如果图片数据包含base64前缀，则去除
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
            
            # 尝试解码以验证是否为有效的base64
            base64.b64decode(image_data)
        except Exception as e:
            return [{"error": f"无效的图片数据: {str(e)}"} ]
        
        # 调用淘宝API进行图片搜索
        products = taobao_api.search_by_image(image_data)
        
        # 转换为字典列表
        return [self._format_product(product) for product in products]
    
    def _format_product(self, product) -> Dict[str, Any]:
        """格式化商品信息"""
        return {
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