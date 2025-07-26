#!/usr/bin/env python3
"""
测试监控功能的脚本
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, description):
    """测试单个端点"""
    print(f"\n🔍 测试 {description}")
    print(f"📍 端点: {endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"✅ 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 响应数据预览:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
        else:
            print(f"❌ 错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试监控功能...")
    
    # 测试基础健康检查
    test_endpoint("/health", "基础健康检查")
    
    # 测试模型健康检查
    test_endpoint("/api/v1/health/model", "AI模型健康检查")
    
    # 测试系统指标
    test_endpoint("/api/v1/health/system", "系统指标")
    
    # 测试性能状态
    test_endpoint("/api/v1/health/performance", "性能状态")
    
    # 测试完整指标
    test_endpoint("/api/v1/health/metrics", "完整指标")
    
    print("\n🎉 监控功能测试完成！")
    print("💡 提示: 你可以在浏览器中访问这些端点来查看详细信息")
    print(f"🌐 主页: {BASE_URL}")
    print(f"📊 系统指标: {BASE_URL}/api/v1/health/system")
    print(f"⚡ 性能状态: {BASE_URL}/api/v1/health/performance")

if __name__ == "__main__":
    main()