import requests
import json
import base64
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试用户凭据
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_EMAIL = "test@example.com"

# 存储访问令牌
access_token = None


def test_register():
    """测试用户注册"""
    print("\n测试用户注册...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    return response.status_code == 200


def test_login():
    """测试用户登录"""
    global access_token
    print("\n测试用户登录...")
    response = requests.post(
        f"{BASE_URL}/auth/login/json",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        return True
    return False


def test_chat():
    """测试聊天功能"""
    global access_token
    if not access_token:
        print("未登录，无法测试聊天功能")
        return False
    
    print("\n测试聊天功能...")
    response = requests.post(
        f"{BASE_URL}/chat/send",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "session_id": None,  # 新会话
            "message": "你好，我想找一些运动鞋",
            "message_type": "text"
        }
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        
        # 测试获取会话消息
        print("\n测试获取会话消息...")
        response = requests.get(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        return True
    return False


def test_product_search():
    """测试商品搜索功能"""
    global access_token
    if not access_token:
        print("未登录，无法测试商品搜索功能")
        return False
    
    print("\n测试商品搜索功能...")
    response = requests.get(
        f"{BASE_URL}/product/search",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"query": "运动鞋", "page": 1, "limit": 5}
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    return response.status_code == 200


def main():
    """运行所有测试"""
    print("开始API测试...\n")
    
    # 测试注册
    register_success = test_register()
    if not register_success:
        print("注册测试失败，尝试直接登录")
    
    # 测试登录
    login_success = test_login()
    if not login_success:
        print("登录测试失败，无法继续测试")
        return
    
    # 测试聊天
    chat_success = test_chat()
    if not chat_success:
        print("聊天测试失败")
    
    # 测试商品搜索
    search_success = test_product_search()
    if not search_success:
        print("商品搜索测试失败")
    
    print("\nAPI测试完成")


if __name__ == "__main__":
    main()