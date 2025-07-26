# 淘宝API配置说明

## 概述
本项目已经实现了真实的淘宝API调用功能，但需要正确的配置才能正常工作。

## 配置要求

### 1. 淘宝开放平台账号
- 访问 [淘宝开放平台](https://open.taobao.com/)
- 注册开发者账号
- 创建应用获取 `app_key` 和 `app_secret`

### 2. 淘宝客推广位
- 需要申请成为淘宝客
- 在淘宝联盟后台创建推广位
- 获取 `adzone_id`（推广位ID）

### 3. 环境变量配置
在 `.env` 文件中配置：
```
TAOBAO_APP_KEY=你的应用Key
TAOBAO_APP_SECRET=你的应用Secret
TAOBAO_ADZONE_ID=你的推广位ID
```

## API接口说明

### search_material 方法
- **功能**: 搜索淘宝商品物料
- **API**: `taobao.tbk.dg.material.optional.upgrade`
- **参数**:
  - `q`: 搜索关键词
  - `page_no`: 页码（从1开始）
  - `page_size`: 每页商品数量
  - `adzone_id`: 推广位ID（必需）
  - `material_id`: 物料ID

### 错误处理
- 当API调用失败时，会自动返回模拟数据作为备用
- 所有错误都会记录到日志中
- 支持超时、连接错误等异常处理

## 测试
运行 `python3 test_taobao_api.py` 来测试API调用。

## 注意事项
1. 淘宝API有调用频率限制
2. 需要有效的淘宝客账号和推广位
3. 某些API可能需要特殊权限
4. 建议在生产环境中配置真实的密钥

## 当前状态
- ✅ API调用框架已完成
- ✅ 错误处理和日志记录已实现
- ✅ 备用数据机制已实现
- ⚠️ 需要配置有效的推广位ID