"""Middleware for structured request/response logging."""
import time
import uuid
import logging
import json
from typing import Callable # Keep Callable for dispatch method
from logstash_async.handler import AsynchronousLogstashHandler
from fastapi import Request, Response # Keep Response for dispatch method
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

# Setup logger
logger = logging.getLogger("shorty")
logger.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Logstash Handler (TCP)
# Use host.docker.internal to reach Logstash running on Docker Compose from K8s
logstash_handler = AsynchronousLogstashHandler(
    host='host.docker.internal',
    port=5001,
    database_path=None
)
logger.addHandler(logstash_handler)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            execution_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "execution_time": f"{execution_time:.3f}s",
                    "error": str(e),
                },
                exc_info=True
            )
            raise
        
        # Log response
        execution_time = time.time() - start_time
        
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "execution_time": f"{execution_time:.3f}s",
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
