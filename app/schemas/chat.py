from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


class MessageBase(BaseModel):
    role: str
    content: str
    message_type: str = "text"  # text, image, product
    metadata: Optional[Dict[Any, Any]] = None


class MessageCreate(MessageBase):
    session_id: int


class Message(MessageBase):
    id: int
    session_id: int
    created_at: datetime

    @classmethod
    def from_orm(cls, obj):
        """自定义 ORM 对象转换，处理 extra_data 到 metadata 的映射"""
        # 获取基本字段
        data = {
            'id': obj.id,
            'session_id': obj.session_id,
            'role': obj.role,
            'content': obj.content,
            'message_type': obj.message_type,
            'created_at': obj.created_at,
            'metadata': obj.extra_data  # 将 extra_data 映射到 metadata
        }
        return cls(**data)

    @validator('metadata', pre=True, always=True)
    def validate_metadata(cls, v):
        """确保 metadata 始终是字典类型"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        # 如果是其他类型，尝试转换为字典或返回 None
        try:
            if hasattr(v, '__dict__'):
                return v.__dict__
            return None
        except:
            return None

    class Config:
        from_attributes = True  # Pydantic V2 替代 orm_mode
        
        @staticmethod
        def json_schema_extra(schema: Dict[str, Any], model_type) -> None:
            """自定义 schema - Pydantic V2"""
            if 'properties' in schema and 'metadata' in schema['properties']:
                schema['properties']['metadata']['type'] = 'object'


class SessionBase(BaseModel):
    title: str = "新会话"
    is_active: bool = True


class SessionCreate(SessionBase):
    user_id: int


class SessionUpdate(SessionBase):
    pass


class Session(SessionBase):
    id: int
    user_id: int
    created_at: datetime
    messages: List[Message] = []

    @classmethod
    def from_orm(cls, obj):
        """自定义 ORM 对象转换，避免序列化问题"""
        # 获取基本字段，不包含 messages 以避免循环加载
        data = {
            'id': obj.id,
            'user_id': obj.user_id,
            'title': obj.title,
            'is_active': obj.is_active,
            'created_at': obj.created_at,
            'messages': []  # 默认为空列表，避免自动加载消息
        }
        return cls(**data)

    class Config:
        from_attributes = True  # Pydantic V2 替代 orm_mode


class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: Optional[int] = None
    message: str
    message_type: str = "text"  # text, image, product
    metadata: Optional[Dict[Any, Any]] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: int
    message: str
    message_type: str = "text"  # text, image, product
    metadata: Optional[Dict[Any, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImageSearchRequest(BaseModel):
    """图片搜索请求模型"""
    session_id: Optional[int] = None
    image_data: str  # Base64编码的图片数据
    message: Optional[str] = None


class ProductQuery(BaseModel):
    """商品查询请求模型"""
    query: str
    category: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    sort: Optional[str] = None  # price_asc, price_desc, sales_desc
    page: int = 1
    page_size: int = 10


class ProductBase(BaseModel):
    """商品基础模型"""
    item_id: str
    title: str
    price: str
    original_price: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    detail_url: Optional[str] = None
    category: Optional[str] = None
    shop_name: Optional[str] = None
    rating: Optional[str] = None
    sales: Optional[str] = None
    metadata: Optional[Dict[Any, Any]] = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic V2 替代 orm_mode


class ProductSearchResponse(BaseModel):
    """商品搜索响应模型"""
    products: List[ProductBase]
    total: int
    page: int
    page_size: int