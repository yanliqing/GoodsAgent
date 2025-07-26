from typing import Dict, Any
from langchain.tools import BaseTool

from app.services.taobao import taobao_api


class OrderInfoTool(BaseTool):
    """用于查询订单信息的工具"""
    
    name: str = "order_info"
    description: str = "查询淘宝订单的详细信息，包括订单状态、支付信息、商品列表等"
    
    def _run(self, order_id: str) -> Dict[str, Any]:
        """查询订单信息"""
        # 调用淘宝API获取订单信息
        order_info = taobao_api.get_order_info(order_id)
        
        if not order_info:
            return {"error": "未找到订单信息"}
        
        return order_info


class LogisticsInfoTool(BaseTool):
    """用于查询物流信息的工具"""
    
    name: str = "logistics_info"
    description: str = "查询淘宝订单的物流信息，包括物流状态、配送进度等"
    
    def _run(self, order_id: str) -> Dict[str, Any]:
        """查询物流信息"""
        # 调用淘宝API获取物流信息
        logistics_info = taobao_api.get_logistics_info(order_id)
        
        if not logistics_info:
            return {"error": "未找到物流信息"}
        
        return logistics_info