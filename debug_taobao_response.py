#!/usr/bin/env python3
"""
调试淘宝API响应结构
"""
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.taobao import taobao_api
from app.core.config import settings

def debug_api_response():
    print("=" * 50)
    print("调试淘宝API响应结构")
    print("=" * 50)
    
    # 检查配置
    print(f"App Key: {settings.TAOBAO_APP_KEY}")
    print(f"App Secret: {'*' * len(settings.TAOBAO_APP_SECRET) if settings.TAOBAO_APP_SECRET else 'Not Set'}")
    print(f"Adzone ID: {settings.TAOBAO_ADZONE_ID or 'Not Set'}")
    print(f"Material ID: {settings.TAOBAO_MATERIAL_ID}")
    print()
    
    if not settings.TAOBAO_APP_KEY or not settings.TAOBAO_APP_SECRET:
        print("❌ 淘宝API密钥未配置")
        return
    
    # 直接调用API方法查看响应
    method = "taobao.tbk.dg.material.optional.upgrade"
    params = {
        "q": "手机",
        "page_no": 1,
        "page_size": 3,
        "adzone_id": settings.TAOBAO_ADZONE_ID or "123456789",
        "material_id": settings.TAOBAO_MATERIAL_ID or "13366",
        "has_coupon": "false",
        "ip": "127.0.0.1",
        "platform": "1",
        "cat": "",
        "itemloc": "",
        "sort": "total_sales_des",
    }
    
    try:
        print("🔍 调用API...")
        response = taobao_api._request(method, params)
        print("✅ API调用成功")
        print()
        
        print("📋 完整API响应:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print()
        
        # 分析响应结构
        if isinstance(response, dict):
            print("🔍 响应键分析:")
            for key in response.keys():
                print(f"  - {key}")
                if key == "tbk_dg_material_optional_upgrade_response":
                    data = response[key]
                    print(f"    类型: {type(data)}")
                    if isinstance(data, dict):
                        print("    子键:")
                        for subkey in data.keys():
                            print(f"      - {subkey}: {type(data[subkey])}")
                            if subkey == "result_list" and isinstance(data[subkey], dict):
                                result_list = data[subkey]
                                print("        result_list 子键:")
                                for rlkey in result_list.keys():
                                    print(f"          - {rlkey}: {type(result_list[rlkey])}")
                                    if rlkey == "map_data" and isinstance(result_list[rlkey], list):
                                        map_data = result_list[rlkey]
                                        print(f"            map_data 长度: {len(map_data)}")
                                        if map_data:
                                            print("            第一个商品的键:")
                                            for itemkey in map_data[0].keys():
                                                print(f"              - {itemkey}: {map_data[0][itemkey]}")
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_response()