import hashlib
import time
import json
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from app.core.config import settings
from app.schemas.chat import ProductBase


class TaobaoAPI:
    """淘宝开放平台API封装"""
    
    BASE_URL = "https://eco.taobao.com/router/rest"
    
    def __init__(self):
        self.app_key = settings.TAOBAO_APP_KEY
        self.app_secret = settings.TAOBAO_APP_SECRET
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成API签名"""
        # 按字典序排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接参数
        param_str = self.app_secret
        for k, v in sorted_params:
            param_str += k + str(v)
        param_str += self.app_secret
        # MD5加密
        return hashlib.md5(param_str.encode('utf-8')).hexdigest().upper()
    
    def _prepare_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """准备请求参数"""
        # 公共参数
        base_params = {
            "method": method,
            "app_key": self.app_key,
            "timestamp": str(int(time.time())),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5",
        }
        
        # 合并参数
        all_params = {**base_params, **params}
        
        # 生成签名
        all_params["sign"] = self._generate_signature(all_params)
        
        return all_params
    
    def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送API请求"""
        from app.core.exceptions import TaobaoAPIError
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        
        try:
            request_params = self._prepare_request(method, params)
            
            # 记录API调用日志
            logger.info(f"调用淘宝API: {method}, 参数: {params}")
            
            response = requests.post(
                self.BASE_URL, 
                data=request_params,
                timeout=30  # 设置超时时间
            )
            
            # 检查HTTP状态码
            response.raise_for_status()
            
            result = response.json()
            
            # 记录API响应日志
            if "error_response" in result:
                error_info = result["error_response"]
                logger.error(f"淘宝API错误: {error_info}")
                raise TaobaoAPIError(
                    message=f"淘宝API调用失败: {error_info.get('msg', '未知错误')}",
                    error_code=error_info.get('code', 'UNKNOWN'),
                    details=error_info
                )
            
            logger.info(f"淘宝API调用成功: {method}")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"淘宝API调用超时: {method}")
            raise TaobaoAPIError(
                message="淘宝API调用超时",
                error_code="TIMEOUT"
            )
        except requests.exceptions.ConnectionError:
            logger.error(f"淘宝API连接错误: {method}")
            raise TaobaoAPIError(
                message="无法连接到淘宝API服务器",
                error_code="CONNECTION_ERROR"
            )
        except requests.exceptions.HTTPError as e:
            logger.error(f"淘宝API HTTP错误: {method}, 状态码: {e.response.status_code}")
            raise TaobaoAPIError(
                message=f"淘宝API HTTP错误: {e.response.status_code}",
                error_code="HTTP_ERROR",
                details={"status_code": e.response.status_code}
            )
        except Exception as e:
            logger.error(f"淘宝API调用异常: {method}, 错误: {str(e)}")
            raise TaobaoAPIError(
                message=f"淘宝API调用异常: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    def search_material(self, query: str, page_no: int = 1, page_size: int = 20) -> List[ProductBase]:
        """搜索淘宝物料
        
        使用淘宝物料搜索接口 (taobao.tbk.dg.material.optional.upgrade)
        """
        from app.core.exceptions import TaobaoAPIError
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        
        method = "taobao.tbk.dg.material.optional.upgrade"
        params = {
            "q": query,
            "page_no": page_no,
            "page_size": page_size,
            "adzone_id": settings.TAOBAO_ADZONE_ID or "100812600397",  # 使用配置的推广位ID，如果没有则使用默认值
            "material_id": settings.TAOBAO_MATERIAL_ID or "13366",  # 使用配置的物料ID
            "has_coupon": "false",  # 不限制优惠券
            "ip": "127.0.0.1",  # IP地址
            "platform": "1",  # 平台：1-PC，2-无线
            "cat": "",  # 商品类目ID，空表示不限制
            "itemloc": "",  # 商品所在地，空表示不限制
            "sort": "total_sales_des",  # 排序方式：销量从高到低
        }
        
        try:
            response = self._request(method, params)
            logger.info(f"淘宝API调用成功: {method}")
            logger.info(f"API响应内容: {response}")  # 添加调试信息
            
            # 解析响应
            response_key = "tbk_dg_material_optional_upgrade_response"  # 修正响应键格式
            if response_key not in response:
                logger.warning(f"API响应格式错误: 缺少 {response_key}")
                logger.warning(f"实际响应键: {list(response.keys()) if isinstance(response, dict) else type(response)}")
                return self._get_fallback_products(query, page_size)
            
            response_data = response[response_key]
            
            # 检查是否有结果数据
            if "result_list" not in response_data or not response_data["result_list"]:
                logger.info(f"没有找到相关商品: {query}")
                return self._get_fallback_products(query, page_size)
            
            # 解析商品列表
            result_list = response_data["result_list"]
            products = []
            
            if "map_data" in result_list:
                items = result_list["map_data"]
                
                for item in items:
                    try:
                        # 获取基本信息
                        basic_info = item.get("item_basic_info", {})
                        price_info = item.get("price_promotion_info", {})
                        publish_info = item.get("publish_info", {})
                        
                        # 解析商品信息
                        product = ProductBase(
                            item_id=str(item.get("item_id", "")),
                            title=basic_info.get("title", ""),
                            price=str(price_info.get("zk_final_price", "0")),
                            original_price=str(price_info.get("reserve_price", "0")),
                            description=basic_info.get("sub_title", ""),
                            image_url=basic_info.get("pict_url", "").replace("_300x300.jpg", "_400x400.jpg"),
                            detail_url=publish_info.get("click_url", ""),
                            category=basic_info.get("level_one_category_name", ""),
                            shop_name=basic_info.get("shop_title", ""),
                            rating="",  # API响应中没有评分信息
                            sales=str(basic_info.get("volume", 0)),
                            metadata={
                                "category_id": basic_info.get("category_id", ""),
                                "level_one_category_id": basic_info.get("level_one_category_id", ""),
                                "seller_id": basic_info.get("seller_id", ""),
                                "user_type": basic_info.get("user_type", ""),
                                "real_post_fee": basic_info.get("real_post_fee", ""),
                                "white_image": basic_info.get("white_image", ""),
                                "small_images": basic_info.get("small_images", {}),
                                "coupon_share_url": publish_info.get("coupon_share_url", ""),
                                "income_rate": publish_info.get("income_rate", ""),
                                "income_info": publish_info.get("income_info", {}),
                                "presale_info": item.get("presale_info", {}),
                                "scope_info": item.get("scope_info", {})
                            }
                        )
                        products.append(product)
                    except Exception as item_error:
                        logger.warning(f"解析商品数据失败: {item_error}")
                        continue
            
            logger.info(f"成功获取 {len(products)} 个商品，查询: {query}")
            return products if products else self._get_fallback_products(query, page_size)
            
        except TaobaoAPIError as e:
            logger.error(f"淘宝API错误: {e.message}")
            # 如果是API错误，返回模拟数据作为备用
            return self._get_fallback_products(query, page_size)
        except Exception as e:
            logger.error(f"搜索物料失败: {e}")
            # 如果是其他错误，也返回模拟数据作为备用
            return self._get_fallback_products(query, page_size)
    
    def _get_fallback_products(self, query: str, page_size: int) -> List[ProductBase]:
        """当API调用失败时返回的备用模拟数据"""
        products = [
            ProductBase(
                item_id=f"fallback_item_{i}",
                title=f"{query}相关商品{i} (模拟数据)",
                price=f"{(100 + i * 10):.2f}",
                original_price=f"{(150 + i * 10):.2f}",
                description=f"{query}商品描述{i} (API调用失败，显示模拟数据)",
                image_url=f"https://example.com/image_{i}.jpg",
                detail_url=f"https://item.taobao.com/item.htm?id={i}",
                category="测试分类",
                shop_name=f"测试店铺{i}",
                rating=f"{4 + i % 2}",
                sales=f"{1000 + i * 100}",
                metadata={
                    "promotion": "满300减30",
                    "shipping": "免运费",
                    "fallback": "true"
                }
            )
            for i in range(1, min(page_size + 1, 6))  # 限制备用数据数量
        ]
        return products
    
    def search_by_image(self, image_data: str) -> List[ProductBase]:
        """通过图片搜索商品
        
        注意：淘宝目前没有直接的图片搜索API，这里模拟实现
        实际应用中可能需要使用其他第三方服务或淘宝官方合作
        """
        # 模拟图片搜索结果
        products = [
            ProductBase(
                item_id=f"img_item_{i}",
                title=f"图片搜索商品{i}",
                price=f"{(120 + i * 15):.2f}",
                original_price=f"{(180 + i * 15):.2f}",
                description=f"与图片相似的商品{i}",
                image_url=f"https://example.com/similar_image_{i}.jpg",
                detail_url=f"https://item.taobao.com/item.htm?id=img_{i}",
                category="图片搜索",
                shop_name=f"图片商品店铺{i}",
                rating=f"{4.5}",
                sales=f"{800 + i * 120}",
                metadata={
                    "similarity": f"{90 - i * 5}%",
                    "promotion": "新品促销"
                }
            )
            for i in range(1, 6)
        ]
        return products
    
    def get_product_details(self, item_id: str) -> Optional[ProductBase]:
        """获取商品详情
        
        使用淘宝商品详情API (taobao.item.get)
        """
        method = "taobao.item.get"
        params = {
            "num_iid": item_id,
            "fields": "num_iid,title,price,original_price,desc,pic_url,detail_url,cid,seller_cids,props,props_name"
        }
        
        try:
            # 模拟API响应，实际使用时替换为真实API调用
            # result = self._request(method, params)
            
            # 模拟数据，实际使用时应解析API返回的数据
            return ProductBase(
                item_id=item_id,
                title=f"商品详情{item_id}",
                price="199.00",
                original_price="299.00",
                description="这是一个测试商品的详细描述，包含了商品的各种特性和使用方法。",
                image_url="https://example.com/detail_image.jpg",
                detail_url=f"https://item.taobao.com/item.htm?id={item_id}",
                category="详情测试分类",
                shop_name="详情测试店铺",
                rating="4.8",
                sales="2500",
                metadata={
                    "brand": "测试品牌",
                    "material": "高级材质",
                    "size": "均码",
                    "color": "多色可选",
                    "shipping": "免运费",
                    "return_policy": "7天无理由退换"
                }
            )
        except Exception as e:
            print(f"获取商品详情失败: {e}")
            return None
    
    def get_logistics_info(self, order_id: str) -> Dict[str, Any]:
        """获取物流信息
        
        模拟物流查询功能
        """
        # 模拟物流信息
        return {
            "order_id": order_id,
            "logistics_company": "测试快递",
            "tracking_number": f"YT{order_id}2023",
            "status": "运输中",
            "details": [
                {"time": "2023-11-10 10:00:00", "description": "包裹已被揽收"},
                {"time": "2023-11-10 16:30:00", "description": "包裹到达分拣中心"},
                {"time": "2023-11-11 08:15:00", "description": "包裹正在配送中"}
            ]
        }
    
    def get_order_info(self, order_id: str) -> Dict[str, Any]:
        """获取订单信息
        
        模拟订单查询功能
        """
        # 模拟订单信息
        return {
            "order_id": order_id,
            "status": "已付款",
            "create_time": "2023-11-09 14:30:00",
            "pay_time": "2023-11-09 14:35:00",
            "total_amount": "299.00",
            "actual_payment": "269.00",
            "discount": "30.00",
            "buyer": "test_user",
            "items": [
                {
                    "item_id": "test_item_1",
                    "title": "测试商品1",
                    "price": "199.00",
                    "quantity": 1
                },
                {
                    "item_id": "test_item_2",
                    "title": "测试商品2",
                    "price": "100.00",
                    "quantity": 1
                }
            ],
            "shipping_address": "测试地址",
            "logistics_status": "运输中"
        }