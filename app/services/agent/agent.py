from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import BaseTool
from langchain import hub

from app.core.config import settings
from app.services.model_factory import ModelFactory
from app.services.agent.tools import (
    ProductSearchTool,
    ProductDetailTool,
    ImageSearchTool,
    OrderInfoTool,
    LogisticsInfoTool,
)


class TaobaoAgent:
    """淘宝智能搜索助手"""
    
    def __init__(self, session_id: Optional[int] = None):
        """初始化智能体
        
        Args:
            session_id: 会话ID，用于关联对话历史
        """
        self.session_id = session_id
        
        # 使用模型工厂创建AI模型
        try:
            self.llm = ModelFactory.create_model()
        except (ValueError, ImportError) as e:
            # 如果当前配置的模型不可用，回退到OpenAI
            print(f"警告: 无法创建 {settings.MODEL_PROVIDER} 模型: {e}")
            print("回退到 OpenAI 模型...")
            self.llm = ModelFactory.create_model(provider="openai")
        
        self.tools = self._get_tools()
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        self.agent = self._create_agent()
    
    def _get_tools(self) -> List[BaseTool]:
        """获取所有可用工具"""
        return [
            ProductSearchTool(),
            ProductDetailTool(),
            ImageSearchTool(),
            OrderInfoTool(),
            LogisticsInfoTool(),
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """创建智能体执行器"""
        # 创建自定义提示模板，兼容不同类型的模型
        template = """你是一个专业的淘宝购物助手，可以帮助用户搜索商品、查询商品信息、提供购物建议、查询订单和物流信息等。

你可以使用以下工具：
{tools}

工具描述：
{tool_names}

在回答用户问题时，请遵循以下原则：
1. 保持友好、专业的语气
2. 提供准确、有用的信息
3. 当用户询问商品时，主动提供价格、评分、销量等关键信息
4. 当用户要求推荐商品时，根据用户需求提供合适的选择
5. 当信息不足时，礼貌地询问用户更多细节
6. 不要编造不存在的信息

使用以下格式回答：

Question: 用户的问题
Thought: 我需要思考如何回答这个问题
Action: 要使用的工具名称
Action Input: 工具的输入参数
Observation: 工具的输出结果
... (这个思考/行动/观察的过程可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 对用户的最终回答

开始！

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        # 创建ReAct智能体（兼容所有模型类型）
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        # 创建执行器
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            early_stopping_method="generate"
        )
    
    async def process_message(self, message: str, message_type: str = "text", metadata: Optional[Dict[Any, Any]] = None) -> Dict[str, Any]:
        """处理用户消息
        
        Args:
            message: 用户消息内容
            message_type: 消息类型，可以是text或image
            metadata: 额外的元数据，如图片数据
        
        Returns:
            智能体的响应
        """
        try:
            # 处理图片搜索
            if message_type == "image" and metadata and "image_data" in metadata:
                # 调用图片搜索工具
                image_tool = ImageSearchTool()
                results = image_tool._run(metadata["image_data"])
                
                # 构建响应消息
                if results and not any("error" in r for r in results):
                    products_info = "\n\n".join([f"商品: {p['title']}\n价格: {p['price']}\n相似度: {p['similarity']}" for p in results[:5]])
                    response_message = f"我找到了一些与您图片相似的商品:\n\n{products_info}\n\n您对这些商品有兴趣吗？或者您想了解更多关于某个特定商品的信息？"
                else:
                    response_message = "抱歉，我无法识别这张图片或找不到相似的商品。您可以尝试上传另一张图片，或者直接告诉我您想找什么类型的商品？"
                
                return {
                    "message": response_message,
                    "message_type": "text",
                    "metadata": {"products": results[:5] if results else []}
                }
            
            # 处理文本消息
            response = await self.agent.ainvoke({
                "input": message
            })
            
            return {
                "message": response["output"],
                "message_type": "text",
                "metadata": {}
            }
        
        except Exception as e:
            # 处理错误
            error_message = f"抱歉，处理您的请求时出现了问题: {str(e)}"
            return {
                "message": error_message,
                "message_type": "text",
                "metadata": {"error": str(e)}
            }