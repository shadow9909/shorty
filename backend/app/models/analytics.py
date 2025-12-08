from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from uuid import uuid4
from app.db import Base


class Analytics(Base):
    """Analytics model for tracking URL clicks."""
    
    __tablename__ = "analytics"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    url_id: Mapped[str] = mapped_column(String(36), ForeignKey("urls.id", ondelete="CASCADE"), nullable=False, index=True)
    
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 max length
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    url: Mapped["URL"] = relationship("URL", back_populates="analytics")
    
    def __repr__(self) -> str:
        return f"<Analytics(id={self.id}, url_id={self.url_id}, clicked_at={self.clicked_at})>"