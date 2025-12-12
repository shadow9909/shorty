"""URL management API endpoints."""
from typing import Optional
import logging 
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.db.repositories import URLRepository, UserRepository
from app.schemas import URLCreate, URLResponse, URLListResponse
from app.services import generate_unique_short_code, is_valid_short_code
from app.services.auth import verify_token

router = APIRouter(prefix="/api/urls", tags=["URLs"])
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[str]:
    """Extract user ID from JWT token (optional authentication).
    
    Returns:
        User ID if authenticated, None if not
    """
    if not credentials:
        return None
    
    # Verify token (credentials.credentials contains the actual token)
    payload = verify_token(credentials.credentials)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    
    # Verify user exists
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user or not user.is_active:
        return None
    
    return user_id


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """Require authentication (raises 401 if not authenticated).
    
    Returns:
        User ID
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    
    # Verify user exists
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


@router.post("/", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    url_data: URLCreate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Create a new short URL.
    
    - **long_url**: The URL to shorten (must be valid HTTP/HTTPS)
    - **custom_alias**: Optional custom short code (3-10 alphanumeric chars)
    - **expires_at**: Optional expiration datetime
    
    Authentication is optional for creating URLs.
    Custom aliases require authentication.
    """
    # Validate: custom alias requires authentication
    logger.error(f"Creating URL - User ID: {user_id}, Long URL: {url_data.long_url}")

    if not user_id and url_data.custom_alias:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to create custom aliases",
            headers={"WWW-Authenticate": "Bearer"},
        )
    url_repo = URLRepository(db)
    
    # Get existing short codes for collision detection
    existing_codes = await url_repo.get_all_short_codes()
    
    # Generate or validate short code
    try:
        short_code = generate_unique_short_code(
            existing_codes=existing_codes,
            custom_alias=url_data.custom_alias
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not short_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate unique short code, please try again"
        )
    
    # Create URL in database
    url = await url_repo.create(
        short_code=short_code,
        long_url=str(url_data.long_url),
        user_id=user_id,  # This should now populate correctly
        expires_at=url_data.expires_at
    )
    
    return url

@router.get("/", response_model=URLListResponse)
async def list_my_urls(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth)
):
    """List URLs created by the authenticated user.
    
    Requires authentication.
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )
    
    url_repo = URLRepository(db)
    skip = (page - 1) * page_size
    
    urls, total = await url_repo.get_by_user(
        user_id=user_id,
        skip=skip,
        limit=page_size
    )
    
    has_next = (skip + len(urls)) < total
    
    return URLListResponse(
        urls=urls,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next
    )


@router.get("/{short_code}", response_model=URLResponse)
async def get_url_info(
    short_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get information about a short URL (without redirecting).
    
    Returns URL details including click count and creation date.
    """
    if not is_valid_short_code(short_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid short code format"
        )
    
    url_repo = URLRepository(db)
    url = await url_repo.get_by_short_code(short_code)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
    
    return url


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_auth)
):
    """Delete a short URL (soft delete).
    
    Requires authentication. Users can only delete their own URLs.
    """
    if not is_valid_short_code(short_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid short code format"
        )
    
    url_repo = URLRepository(db)
    url = await url_repo.get_by_short_code(short_code)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
    
    # Check ownership
    if url.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own URLs"
        )
    
    # Soft delete (sets is_active=False)
    await url_repo.delete(url)
    
    return None