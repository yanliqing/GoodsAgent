from typing import Dict, Any
from langchain.tools import BaseTool
import logging

from app.services.taobao import taobao_api

logger = logging.getLogger(__name__)


class OrderInfoTool(BaseTool):
    """用于查询订单信息的工具"""
    
    name: str = "order_info"
    description: str = "查询淘宝订单的详细信息，包括订单状态、支付信息、商品列表等"
    
    def _run(self, order_id: str) -> Dict[str, Any]:
        """查询订单信息"""
        logger.info("📋 OrderInfoTool 开始查询订单信息")
        logger.info(f"🆔 订单ID: {order_id}")
        
        try:
            # 调用淘宝API获取订单信息
            logger.info("🔄 调用淘宝API获取订单信息...")
            order_info = taobao_api.get_order_info(order_id)
            
            if not order_info:
                logger.warning("⚠️ 未找到订单信息")
                return {"error": "未找到订单信息"}
            
            logger.info("✅ 成功获取订单信息")
            logger.info(f"📦 订单信息概览: {str(order_info)[:100]}...")
            
            return order_info
            
        except Exception as e:
            logger.error("❌ OrderInfoTool 执行失败")
            logger.error(f"🚨 错误详情: {str(e)}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            return {"error": f"查询订单信息失败: {str(e)}"}


class LogisticsInfoTool(BaseTool):
    """用于查询物流信息的工具"""
    
    name: str = "logistics_info"
    description: str = "查询淘宝订单的物流信息，包括物流状态、配送进度等"
    
    def _run(self, order_id: str) -> Dict[str, Any]:
        """查询物流信息"""
        logger.info("🚚 LogisticsInfoTool 开始查询物流信息")
        logger.info(f"🆔 订单ID: {order_id}")
        
        try:
            # 调用淘宝API获取物流信息
            logger.info("🔄 调用淘宝API获取物流信息...")
            logistics_info = taobao_api.get_logistics_info(order_id)
            
            if not logistics_info:
                logger.warning("⚠️ 未找到物流信息")
                return {"error": "未找到物流信息"}
            
            logger.info("✅ 成功获取物流信息")
            logger.info(f"📦 物流信息概览: {str(logistics_info)[:100]}...")
            
            return logistics_info
            
        except Exception as e:
            logger.error("❌ LogisticsInfoTool 执行失败")
            logger.error(f"🚨 错误详情: {str(e)}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            return {"error": f"查询物流信息失败: {str(e)}"}