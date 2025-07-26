from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(default=False, description="请求是否成功")
    message: str = Field(description="错误消息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    total: int = Field(description="总记录数")
    total_pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    data: List[T] = Field(description="响应数据列表")
    meta: PaginationMeta = Field(description="分页元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="服务状态")
    version: str = Field(description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    services: Dict[str, bool] = Field(description="各服务状态")
    uptime: Optional[float] = Field(default=None, description="运行时间（秒）")


class ValidationErrorDetail(BaseModel):
    """验证错误详情"""
    field: str = Field(description="字段名")
    message: str = Field(description="错误消息")
    value: Any = Field(description="错误值")


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应"""
    validation_errors: List[ValidationErrorDetail] = Field(description="验证错误列表")


# 响应工厂函数
def success_response(
    data: Any = None, 
    message: str = "操作成功"
) -> BaseResponse:
    """创建成功响应"""
    return BaseResponse(
        success=True,
        message=message,
        data=data
    )


def error_response(
    message: str,
    error_code: Optional[str] = None,
    error_details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        error_details=error_details
    )


def paginated_response(
    data: List[Any],
    page: int,
    page_size: int,
    total: int,
    message: str = "操作成功"
) -> PaginatedResponse:
    """创建分页响应"""
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    )