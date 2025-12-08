"""Analytics repository for database operations."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Analytics


class AnalyticsRepository:
    """Repository for Analytics database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        url_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None
    ) -> Analytics:
        """Record a URL click event."""
        analytics = Analytics(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)
        return analytics