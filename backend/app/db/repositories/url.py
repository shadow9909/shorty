"""URL repository for database operations."""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models import URL


class URLRepository:
    """Repository for URL database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, url_id: str) -> Optional[URL]:
        """Get URL by ID."""
        result = await self.db.execute(select(URL).where(URL.id == url_id))
        return result.scalar_one_or_none()
    
    async def get_by_short_code(self, short_code: str) -> Optional[URL]:
        """Get URL by short code."""
        result = await self.db.execute(
            select(URL).where(
                and_(
                    URL.short_code == short_code,
                    URL.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_short_codes(self) -> set[str]:
        """Get all existing short codes (for collision detection)."""
        result = await self.db.execute(select(URL.short_code))
        return {row[0] for row in result.all()}
    
    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[URL], int]:
        """Get URLs created by a user with pagination.
        
        Returns:
            Tuple of (urls, total_count)
        """
        # Get total count
        count_result = await self.db.execute(
            select(func.count(URL.id)).where(URL.user_id == user_id)
        )
        total = count_result.scalar_one()
        
        # Get paginated results
        result = await self.db.execute(
            select(URL)
            .where(URL.user_id == user_id)
            .order_by(URL.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        urls = result.scalars().all()
        
        return list(urls), total
    
    async def create(
        self,
        short_code: str,
        long_url: str,
        user_id: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> URL:
        """Create a new URL mapping."""
        url = URL(
            short_code=short_code,
            long_url=long_url,
            user_id=user_id,
            expires_at=expires_at
        )
        self.db.add(url)
        await self.db.commit()
        await self.db.refresh(url)
        return url
    
    async def increment_click_count(self, url: URL) -> None:
        """Increment click count and update last accessed time."""
        url.click_count += 1
        url.last_accessed_at = datetime.utcnow()
        await self.db.commit()
    
    async def update(self, url: URL) -> URL:
        """Update an existing URL."""
        await self.db.commit()
        await self.db.refresh(url)
        return url
    
    async def delete(self, url: URL) -> None:
        """Delete a URL (soft delete by setting is_active=False)."""
        url.is_active = False
        await self.db.commit()
    
    async def hard_delete(self, url: URL) -> None:
        """Permanently delete a URL."""
        await self.db.delete(url)
        await self.db.commit()