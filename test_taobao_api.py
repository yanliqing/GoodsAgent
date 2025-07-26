#!/usr/bin/env python3
"""
测试淘宝API真实调用
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.taobao import taobao_api
from app.core.config import settings

def test_taobao_api():
    """测试淘宝API调用"""
    print("=" * 50)
    print("测试淘宝API真实调用")
    print("=" * 50)
    
    # 检查配置
    print(f"App Key: {settings.TAOBAO_APP_KEY}")
    print(f"App Secret: {'*' * len(settings.TAOBAO_APP_SECRET) if settings.TAOBAO_APP_SECRET else 'Not Set'}")
    print(f"Adzone ID: {settings.TAOBAO_ADZONE_ID or 'Not Set (using default)'}")
    print()
    
    if not settings.TAOBAO_APP_KEY or not settings.TAOBAO_APP_SECRET:
        print("❌ 淘宝API密钥未配置，请在.env文件中设置TAOBAO_APP_KEY和TAOBAO_APP_SECRET")
        return
    
    if not settings.TAOBAO_ADZONE_ID:
        print("⚠️  推广位ID未配置，将使用默认值。建议在.env文件中设置TAOBAO_ADZONE_ID")
        print("   请参考 TAOBAO_API_CONFIG.md 了解如何获取推广位ID")
        print()
    
    # 测试搜索功能
    test_queries = ["手机", "笔记本电脑", "运动鞋"]
    
    for query in test_queries:
        print(f"🔍 搜索商品: {query}")
        try:
            products = taobao_api.search_material(query, page_size=3)
            
            if products:
                print(f"✅ 成功获取 {len(products)} 个商品")
                for i, product in enumerate(products, 1):
                    print(f"  {i}. {product.title}")
                    print(f"     价格: ¥{product.price}")
                    print(f"     店铺: {product.shop_name}")
                    print(f"     销量: {product.sales}")
                    
                    # 检查是否是备用数据
                    if product.metadata.get("fallback") == "true":
                        print(f"     ⚠️  这是备用模拟数据")
                    else:
                        print(f"     ✅ 这是真实API数据")
                    print()
            else:
                print("❌ 没有找到商品")
                
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_taobao_api()