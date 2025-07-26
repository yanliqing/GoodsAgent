from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import BaseTool
from langchain import hub

from app.core.config import settings
from app.core.logging import get_logger
from app.services.model_factory import ModelFactory
from app.services.agent.tools import (
    ProductSearchTool,
    ProductDetailTool,
    ImageSearchTool,
    OrderInfoTool,
    LogisticsInfoTool,
)

logger = get_logger(__name__)


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
            logger.warning(f"无法创建 {settings.MODEL_PROVIDER} 模型: {e}")
            logger.info("回退到 OpenAI 模型...")
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

请严格按照以下格式回答，每个部分都必须包含：

Question: 用户的问题
Thought: 我需要思考如何回答这个问题
Action: 要使用的工具名称
Action Input: 工具的输入参数
Observation: 工具的输出结果
... (这个思考/行动/观察的过程可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 对用户的最终回答

重要格式要求：
- 必须先写"Thought:"然后是你的思考内容
- 如果需要使用工具，下一行必须写"Action:"然后是工具名称
- 工具名称后的下一行必须写"Action Input:"然后是输入参数
- 工具执行后会有"Observation:"和结果
- 最后必须写"Thought:"总结，然后"Final Answer:"给出最终回答
- 不要在格式标识符前后添加额外的文字

示例：
Question: 帮我找一些运动鞋
Thought: 用户想要运动鞋推荐，我需要搜索相关商品
Action: product_search
Action Input: 运动鞋
Observation: [搜索结果]
Thought: 我已经找到了相关的运动鞋，现在可以给出推荐
Final Answer: 根据您的需求，我为您推荐以下运动鞋...

开始！

Question: {input}
{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        # 创建ReAct智能体（兼容所有模型类型）
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        # 创建执行器，增强错误处理
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors="Check your output and make sure it conforms to the format instructions. Make sure to include 'Action:' after 'Thought:' when using tools.",
            max_iterations=3,
            return_intermediate_steps=True
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
        logger.info("=" * 80)
        logger.info("🤖 智能体开始处理消息")
        logger.info(f"📝 消息内容: {message}")
        logger.info(f"📋 消息类型: {message_type}")
        logger.info(f"📊 元数据: {metadata}")
        logger.info(f"🆔 会话ID: {self.session_id}")
        logger.info("=" * 80)
        
        try:
            # 处理图片搜索
            if message_type == "image" and metadata and "image_data" in metadata:
                logger.info("🖼️ 处理图片搜索请求")
                logger.info(f"📊 图片数据大小: {len(metadata['image_data'])} 字符")
                
                # 调用图片搜索工具
                image_tool = ImageSearchTool()
                logger.info("🔧 调用图片搜索工具")
                results = image_tool._run(metadata["image_data"])
                logger.info(f"📊 图片搜索结果数量: {len(results) if results else 0}")
                
                # 构建响应消息
                if results and not any("error" in r for r in results):
                    response_message = f"我找到了 {len(results[:5])} 个与您图片相似的商品，请查看下方的商品推荐："
                    logger.info(f"✅ 图片搜索成功，返回 {len(results[:5])} 个商品")
                    return {
                        "message": response_message,
                        "message_type": "products",
                        "metadata": {"products": results[:5]}
                    }
                else:
                    response_message = "抱歉，我无法识别这张图片或找不到相似的商品。您可以尝试上传另一张图片，或者直接告诉我您想找什么类型的商品？"
                    logger.warning("⚠️ 图片搜索未找到结果")
                    return {
                        "message": response_message,
                        "message_type": "text",
                        "metadata": {}
                    }
            
            # 处理文本消息
            logger.info("📝 处理文本消息")
            logger.info("🔄 调用智能体执行器...")
            response = await self.agent.ainvoke({
                "input": message
            })
            logger.info("✅ 智能体执行完成")
            logger.info(f"📤 智能体原始响应: {response}")
            
            # 尝试从智能体的中间步骤中提取商品数据
            logger.info("🔍 提取商品数据...")
            products_data = self._extract_products_from_response(response)
            logger.info(f"📊 提取到 {len(products_data)} 个商品")
            
            if products_data:
                # 如果找到了商品数据，返回商品类型的消息
                logger.info("🛍️ 返回商品推荐响应")
                return {
                    "message": f"根据您的需求，我为您推荐以下 {len(products_data)} 个商品：",
                    "message_type": "products",
                    "metadata": {"products": products_data}
                }
            else:
                # 普通文本响应
                agent_response = response.get("output", "抱歉，我无法处理您的请求。")
                logger.info("💬 返回文本响应")
                logger.info(f"📤 响应内容: {agent_response[:100]}...")
                return {
                    "message": agent_response,
                    "message_type": "text",
                    "metadata": {}
                }
        
        except Exception as e:
            # 处理错误
            logger.error("=" * 80)
            logger.error("❌ 智能体处理消息时发生错误")
            logger.error(f"📝 原始消息: {message}")
            logger.error(f"📋 消息类型: {message_type}")
            logger.error(f"🚨 错误详情: {str(e)}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error("=" * 80)
            
            error_message = f"抱歉，处理您的请求时出现了问题: {str(e)}"
            return {
                "message": error_message,
                "message_type": "text",
                "metadata": {"error": str(e)}
            }
    
    def _extract_products_from_response(self, agent_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从智能体响应中提取商品数据
        
        Args:
            agent_response: 智能体的完整响应
            
        Returns:
            商品数据列表
        """
        products = []
        
        # 检查中间步骤中是否有工具调用结果
        if "intermediate_steps" in agent_response:
            for i, step in enumerate(agent_response["intermediate_steps"]):
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # 检查是否是商品搜索工具的结果
                    if hasattr(action, 'tool') and action.tool in ['product_search', 'product_detail']:
                        if isinstance(observation, list) and observation:
                            # 确保每个商品都有必要的字段
                            for j, product in enumerate(observation):
                                if isinstance(product, dict) and 'item_id' in product:
                                    products.append(product)
                        elif isinstance(observation, dict) and 'item_id' in observation:
                            products.append(observation)
        
        return products[:5]  # 最多返回5个商品