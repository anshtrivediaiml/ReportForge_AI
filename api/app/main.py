"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi
from app.config import settings
from app.database import engine, Base
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routers import health, jobs, upload, websocket, download, auth, reports, sharing, analytics
import os

# Create database tables - Import models first to register them
from app.models import Job, User, SharedReport  # Import all models to register them with Base
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered technical report generation platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Session Middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", settings.SESSION_SECRET_KEY)
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(jobs.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(upload.router, prefix=settings.API_V1_PREFIX)
app.include_router(download.router, prefix=settings.API_V1_PREFIX)
app.include_router(sharing.router)
app.include_router(analytics.router)
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    print(f"📊 Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    print(f"🔌 Redis: {settings.REDIS_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    print(f"👋 {settings.APP_NAME} shutting down...")


def custom_openapi():
    """Custom OpenAPI schema with OAuth2 configuration"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered technical report generation platform",
        routes=app.routes,
    )
    
    # Configure OAuth2PasswordBearer security scheme for Swagger UI
    # This MUST match the scheme_name in dependencies/auth.py
    # Swagger UI requires the security scheme to be properly configured
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    # Configure OAuth2PasswordBearer for Swagger UI
    # This is what makes the "Authorize" button work
    openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"] = {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/api/v1/auth/token",
                "scopes": {}
            }
        },
        "description": "OAuth2 password flow. Enter your email as username and password."
    }
    
    # Also add a Bearer scheme as fallback (some Swagger UI versions prefer this)
    openapi_schema["components"]["securitySchemes"]["Bearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT Bearer token. Get token from /api/v1/auth/token endpoint."
    }
    
    # Add security requirements to protected endpoints
    # This makes Swagger UI show the authorization button
    protected_paths = ["/api/v1/upload", "/api/v1/jobs", "/api/v1/auth/me", "/api/v1/auth/logout"]
    
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, details in methods.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                # Add security requirement for protected endpoints
                if any(protected in path for protected in protected_paths):
                    if "security" not in details:
                        # Use both schemes - Swagger UI will try OAuth2PasswordBearer first
                        details["security"] = [
                            {"OAuth2PasswordBearer": []},
                            {"Bearer": []}
                        ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }
