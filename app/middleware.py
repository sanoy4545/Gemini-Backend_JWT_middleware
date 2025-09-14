from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.jwt import verify_access_token
import logging


PUBLIC_PATHS = [
    ("/auth/signup", "POST"),
    ("/auth/send-otp", "POST"),
    ("/auth/verify-otp", "POST"),
    ("/auth/forgot-password", "POST"),
    ("/docs", None),
    ("/openapi", None),
]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        
        for path, method in PUBLIC_PATHS:
            if request.url.path.startswith(path) and (method is None or request.method == method):
                return await call_next(request)
        auth_header = request.headers.get("authorization",None)
        print("Authorization Header:")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"success": False, "message": "Missing or invalid Authorization header"})
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or not parts[1].strip():
            return JSONResponse(status_code=401, content={"success": False, "message": "Malformed Authorization header"})
        token = parts[1].strip()
        payload = verify_access_token(token)
        if not payload or "sub" not in payload:
            return JSONResponse(status_code=401, content={"success": False, "message": "Invalid or expired token"})
        # Attach user info to request.state for downstream use
        request.state.user_mobile = payload["sub"]
        return await call_next(request)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logging.error(f"Unhandled error: {exc}", exc_info=True)
            # In production, return a generic message
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal server error"})
