"""Pydantic schemas for URL-related requests and responses."""
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional


class URLCreate(BaseModel):
    """Schema for creating a short URL."""
    long_url: HttpUrl
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=10, pattern="^[a-zA-Z0-9_-]+$")
    expires_at: Optional[datetime] = None


class URLResponse(BaseModel):
    """Schema for URL data in responses."""
    id: str
    short_code: str
    long_url: str
    click_count: int
    created_at: datetime
    last_accessed_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class URLListResponse(BaseModel):
    """Schema for paginated URL list."""
    urls: list[URLResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class URLStats(BaseModel):
    """Schema for URL statistics."""
    short_code: str
    long_url: str
    click_count: int
    created_at: datetime
    last_accessed_at: Optional[datetime]