from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.jwt import verify_access_token

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check for protected endpoints
        if request.url.path.startswith("/auth") or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"success": False, "message": "Missing or invalid Authorization header"})
        token = auth_header.split(" ", 1)[1]
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
            return JSONResponse(status_code=500, content={"success": False, "message": str(exc)})
