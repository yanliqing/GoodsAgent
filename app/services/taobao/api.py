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
            
            # 记录详细的API调用日志
            logger.info("=" * 80)
            logger.info(f"🚀 开始调用淘宝API")
            logger.info(f"📡 接口名称: {method}")
            logger.info(f"🌐 请求URL: {self.BASE_URL}")
            logger.info(f"📝 业务参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
            logger.info(f"🔧 完整请求参数: {json.dumps({k: v for k, v in request_params.items() if k != 'sign'}, ensure_ascii=False, indent=2)}")
            logger.info(f"🔐 签名: {request_params.get('sign', 'N/A')}")
            logger.info("=" * 80)
            
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
                logger.error("=" * 80)
                logger.error(f"❌ 淘宝API调用失败")
                logger.error(f"📡 接口名称: {method}")
                logger.error(f"🚨 错误信息: {json.dumps(error_info, ensure_ascii=False, indent=2)}")
                logger.error("=" * 80)
                raise TaobaoAPIError(
                    message=f"淘宝API调用失败: {error_info.get('msg', '未知错误')}",
                    error_code=error_info.get('code', 'UNKNOWN'),
                    details=error_info
                )
            
            logger.info("=" * 80)
            logger.info(f"✅ 淘宝API调用成功")
            logger.info(f"📡 接口名称: {method}")
            logger.info(f"📊 响应数据大小: {len(json.dumps(result))} 字符")
            logger.info(f"🔍 响应键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            logger.info("=" * 80)
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
        
        logger.info("🔍 开始搜索淘宝商品")
        logger.info(f"🔤 搜索关键词: {query}")
        logger.info(f"📄 页码: {page_no}, 每页数量: {page_size}")
        
        try:
            response = self._request(method, params)
            
            # 解析响应
            response_key = "tbk_dg_material_optional_upgrade_response"  # 修正响应键格式
            if response_key not in response:
                logger.warning("⚠️ API响应格式错误")
                logger.warning(f"🔍 期望的响应键: {response_key}")
                logger.warning(f"📋 实际响应键: {list(response.keys()) if isinstance(response, dict) else type(response)}")
                logger.warning(f"📄 完整响应内容: {json.dumps(response, ensure_ascii=False, indent=2)}")
                return []  # 直接返回空列表，不返回模拟数据
            
            response_data = response[response_key]
            logger.info(f"📊 API响应数据结构: {list(response_data.keys()) if isinstance(response_data, dict) else 'N/A'}")
            
            # 检查是否有结果数据
            if "result_list" not in response_data or not response_data["result_list"]:
                logger.info(f"📭 没有找到相关商品，关键词: {query}")
                logger.info(f"📄 响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                return []  # 直接返回空列表，不返回模拟数据
            
            # 解析商品列表
            result_list = response_data["result_list"]
            logger.info(f"📋 结果列表结构: {list(result_list.keys()) if isinstance(result_list, dict) else 'N/A'}")
            products = []
            
            if "map_data" in result_list:
                items = result_list["map_data"]
                logger.info(f"🛍️ 获取到 {len(items)} 个商品数据")
                
                for i, item in enumerate(items):
                    try:
                        logger.debug(f"📦 解析第 {i+1} 个商品数据")
                        logger.debug(f"🔍 商品原始数据: {json.dumps(item, ensure_ascii=False, indent=2)}")
                        
                        # 获取基本信息
                        basic_info = item.get("item_basic_info", {})
                        price_info = item.get("price_promotion_info", {})
                        publish_info = item.get("publish_info", {})
                        
                        logger.debug(f"📝 基本信息: {json.dumps(basic_info, ensure_ascii=False, indent=2)}")
                        logger.debug(f"💰 价格信息: {json.dumps(price_info, ensure_ascii=False, indent=2)}")
                        logger.debug(f"🔗 发布信息: {json.dumps(publish_info, ensure_ascii=False, indent=2)}")
                        
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
                        logger.debug(f"✅ 成功解析商品: {product.title} (ID: {product.item_id})")
                    except Exception as item_error:
                        logger.warning(f"⚠️ 解析第 {i+1} 个商品数据失败: {item_error}")
                        logger.warning(f"📄 问题商品数据: {json.dumps(item, ensure_ascii=False, indent=2)}")
                        continue
            
            logger.info("=" * 80)
            logger.info(f"🎉 商品搜索完成")
            logger.info(f"🔤 搜索关键词: {query}")
            logger.info(f"📊 成功获取: {len(products)} 个商品")
            logger.info(f"📋 商品列表:")
            for i, product in enumerate(products[:5]):  # 只显示前5个商品的摘要
                logger.info(f"  {i+1}. {product.title[:50]}... (¥{product.price})")
            if len(products) > 5:
                logger.info(f"  ... 还有 {len(products) - 5} 个商品")
            logger.info("=" * 80)
            return products  # 直接返回真实数据，如果为空就是空列表
            
        except TaobaoAPIError as e:
            logger.error(f"❌ 淘宝API错误: {e.message}")
            logger.error(f"🔤 搜索关键词: {query}")
            # API错误时返回空列表，不返回模拟数据
            return []
        except Exception as e:
            logger.error(f"❌ 搜索物料失败: {e}")
            logger.error(f"🔤 搜索关键词: {query}")
            logger.error(f"📄 错误详情: {str(e)}")
            # 其他错误时也返回空列表，不返回模拟数据
            return []

    
    def search_by_image(self, image_data: str) -> List[ProductBase]:
        """通过图片搜索商品
        
        Args:
            image_data: base64编码的图片数据
            
        Returns:
            商品列表
        """
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        
        logger.info("=" * 80)
        logger.info("🖼️ 开始图片搜索")
        logger.info(f"📊 图片数据大小: {len(image_data)} 字符")
        logger.info("⚠️ 图片搜索功能暂未实现真实API")
        logger.info("=" * 80)
        
        try:
            # 这里应该调用真实的图片搜索API
            # 目前没有真实API，直接返回空列表
            logger.info("📭 返回空结果（未实现真实API）")
            return []
            
        except Exception as e:
            logger.error(f"❌ 图片搜索失败: {e}")
            return []
    
    def get_product_details(self, item_id: str) -> Optional[ProductBase]:
        """获取商品详情
        
        使用淘宝商品详情API (taobao.item.get)
        """
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        
        method = "taobao.item.get"
        params = {
            "num_iid": item_id,
            "fields": "num_iid,title,price,original_price,desc,pic_url,detail_url,cid,seller_cids,props,props_name"
        }
        
        logger.info("=" * 80)
        logger.info("🔍 开始获取商品详情")
        logger.info(f"📡 接口名称: {method}")
        logger.info(f"🆔 商品ID: {item_id}")
        logger.info(f"📝 请求字段: {params['fields']}")
        logger.info("⚠️ 商品详情功能暂未实现真实API")
        logger.info("=" * 80)
        
        try:
            # 这里应该调用真实的商品详情API
            # 目前没有真实API，直接返回 None
            logger.info("📭 返回空结果（未实现真实API）")
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取商品详情失败: {e}")
            return None
    
    def get_logistics_info(self, order_id: str) -> Dict[str, Any]:
        """获取物流信息
        
        物流查询功能
        """
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        
        logger.info("=" * 80)
        logger.info("🚚 开始查询物流信息")
        logger.info(f"📦 订单ID: {order_id}")
        logger.info("⚠️ 物流查询功能暂未实现真实API")
        logger.info("=" * 80)
        
        try:
            # 这里应该调用真实的物流查询API
            # 目前没有真实API，直接返回空字典
            logger.info("📭 返回空结果（未实现真实API）")
            return {}
            
        except Exception as e:
            logger.error(f"❌ 获取物流信息失败: {e}")
            return {}
    
    def get_order_info(self, order_id: str) -> Dict[str, Any]:
        """获取订单信息
        
        订单查询功能
        """
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        
        logger.info("=" * 80)
        logger.info("📋 开始查询订单信息")
        logger.info(f"🆔 订单ID: {order_id}")
        logger.info("⚠️ 订单查询功能暂未实现真实API")
        logger.info("=" * 80)
        
        try:
            # 这里应该调用真实的订单查询API
            # 目前没有真实API，直接返回空字典
            logger.info("📭 返回空结果（未实现真实API）")
            return {}
            
        except Exception as e:
            logger.error(f"❌ 获取订单信息失败: {e}")
            return {}