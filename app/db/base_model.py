from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    # 自动生成表名
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def dict(self) -> Dict[str, Any]:
        """将模型转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}