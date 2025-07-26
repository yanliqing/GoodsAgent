# 淘宝智能搜索助手

这是一个基于LangChain和OpenAI的智能体应用，可以通过对话形式帮助用户搜索淘宝商品、提供商品信息咨询、商品推荐、订单售后咨询和物流查询等功能。

## 功能特点

- **以图搜品**：上传图片查找相似商品
- **商品信息咨询**：询问商品的详细信息
- **商品推荐**：根据用户需求推荐合适的商品
- **订单售后咨询**：处理订单相关问题
- **物流咨询**：查询物流状态

## 技术栈

- **后端框架**：FastAPI
- **AI框架**：LangChain + OpenAI
- **数据库**：SQLite (可扩展到其他数据库)
- **API集成**：淘宝开放平台API

## 安装与设置

1. 克隆仓库

```bash
git clone <repository-url>
cd Agent
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的API密钥和配置信息。

4. 初始化数据库

```bash
python -m app.db.init_db
```

5. 启动应用

```bash
uvicorn app.main:app --reload
```

## 使用方法

应用启动后，可以通过以下方式使用：

- **Web界面**：访问 http://localhost:8000 使用Web界面
- **API接口**：通过 http://localhost:8000/docs 查看API文档

## 项目结构

```
.
├── app/                    # 应用主目录
│   ├── api/                # API路由
│   ├── core/               # 核心配置
│   ├── db/                 # 数据库模型和操作
│   ├── services/           # 业务逻辑服务
│   │   ├── agent/          # 智能体实现
│   │   ├── taobao/         # 淘宝API集成
│   │   └── chat/           # 聊天处理逻辑
│   ├── schemas/            # Pydantic模型
│   └── main.py             # 应用入口
├── alembic/                # 数据库迁移
├── static/                 # 静态文件
├── templates/              # HTML模板
├── tests/                  # 测试
├── .env.example            # 环境变量示例
├── requirements.txt        # 依赖列表
└── README.md               # 项目说明
```

## 开发者指南

### 添加新功能

1. 在 `app/services/agent/tools` 目录下创建新的工具
2. 在 `app/services/agent/agent.py` 中注册新工具
3. 更新相关的API端点和前端界面

### 测试

```bash
python -m pytest
```

## 许可证

[MIT](LICENSE)