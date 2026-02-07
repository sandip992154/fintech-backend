import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from sqlalchemy import text
from pydantic import ValidationError

# Load environment variables
load_dotenv()
from database.database import engine, Base, session_scope, SessionLocal
from services.auth import auth, password_reset
from services.auth.superadmin_auth import authenticate_superadmin, create_superadmin_token
from services.routers import (
    user,
    service,
    additional_services,
    transactions,
    transaction,
    commission,
    kyc
)
from services.routers.mpin_router import router as mpin_router
from services.routers.user_management import router as user_management_router
from services.routers.mpin_management import router as mpin_management_router
from services.routers.profile_management import router as profile_management_router
from services.routers.member_services import router as member_router
from services.routers.member_admin_routes import router as member_admin_router
# Import unified member routes
from services.routers.member_unified_routes import router as member_unified_router


# Import database initialization
from database.init_db import init_superadmin, init_roles

# Create tables
Base.metadata.create_all(bind=engine)

# Import database initialization
from database.init_db import init_superadmin, init_roles

# Initialize logging
from utils.logging_config import setup_logging, RequestResponseLoggingMiddleware

logging_config = {
    "level": "DEBUG",
    "file": "logs/app.log",
    "max_size": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5
}

logger = setup_logging(logging_config)

# Function to initialize database data at server startup
def initialize_database_on_startup():
    """Initialize database with roles and superadmin user when server starts"""
    try:
        logger.info("=== SERVER STARTUP: Initializing Database ===")
        with SessionLocal() as db:
            logger.info("=== SERVER STARTUP: Initializing System Roles ===")
            init_roles(db)
            logger.info("=== SERVER STARTUP: Creating/Updating Superadmin User ===")
            init_superadmin(db)
            logger.info("=== SERVER STARTUP: Database initialization completed ===")
        logger.info("=== SERVER STARTUP: Application ready ===")
        return True
    except Exception as e:
        logger.error(f"=== SERVER STARTUP ERROR: {e} ===")
        raise

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for startup and shutdown
    """
    # Startup: Initialize resources
    logger.info("Starting up Bandaru API...")
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize database with roles and superadmin
        logger.info("Initializing database with roles and superadmin...")
        with session_scope() as db:
            init_superadmin(db)
        logger.info("Database initialization completed")
        
        logger.info("Bandaru API startup completed successfully")
        
        # Signal application startup complete
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise
    finally:
        # Cleanup: Release resources
        logger.info("Shutting down Bandru API...")
        try:
            # Close any active sessions
            await app.state.close_sessions()
            # Dispose engine connections
            engine.dispose()
            logger.info("Database connections closed successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}", exc_info=True)



# Initialize FastAPI app
app = FastAPI(
    title="Bandru Financial Services API",
    description="""
    Bandru Financial Services API provides comprehensive endpoints for:
    * User Authentication and Authorization
    * Transaction Management
    * AEPS Services
    * mATM Services
    * Insurance Services
    * PAN Card Services
    * FASTag Services
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Initialize database with roles and superadmin immediately when server starts
logger.info("=== EXECUTING DATABASE INITIALIZATION ON SERVER START ===")
initialize_database_on_startup()

@app.on_event("startup")
async def startup_event():
    """FastAPI startup event - additional initialization if needed"""
    logger.info("📡 === FASTAPI STARTUP EVENT: Server is ready ===")

@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI shutdown event"""
    logger.info("🛑 === FASTAPI SHUTDOWN EVENT: Server is stopping ===")

# Configure CORS with environment-specific origins
origins = [
    "https://bandarupay.pro",
    "https://www.bandarupay.pro",
    "https://admin.bandarupay.pro",
    "https://customer.bandarupay.pro",
    "https://mds.bandarupay.pro",
    "https://retailer.bandarupay.pro",
    "https://superadmin.bandarupay.pro",
    "https://whitelable.bandarupay.pro",
    "https://backend.bandarupay.pro",
    # Render deployed URLs
    "https://*.render.com",
    "https://fintech-backend-f9vu.onrender.com",
    # Development URLs
    "http://localhost:5172",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://localhost:5179",
    "http://127.0.0.1:5172",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "Accept",
        "Origin", 
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Access-Control-Allow-Origin"
    ],
    expose_headers=[
        "Content-Length",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials"
    ],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Test CORS endpoint
@app.get("/test-cors")
async def test_cors():
    return {"message": "CORS is working!", "status": "success"}


# Add logging middleware
app.add_middleware(RequestResponseLoggingMiddleware, app_logger=logger)

# Include routers first - using /api/v1 prefix for consistency
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(password_reset.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(service.router)
app.include_router(additional_services.router, prefix="/additional-services", tags=["Additional Services"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(transaction.router)
app.include_router(commission.router)
app.include_router(mpin_router)

# Include new routers for enhanced user management
app.include_router(user_management_router, prefix="/api/v1/user-management", tags=["User Management"])
app.include_router(mpin_management_router, prefix="/api/v1/mpin", tags=["MPIN Management"])
app.include_router(profile_management_router, prefix="/api/v1/profile", tags=["Profile Management"])

# Include unified member management router (replaces both core and admin routes)
app.include_router(member_unified_router, tags=["Unified Member Management"])

# Legacy member routes (temporarily disabled for testing unified routes)
# app.include_router(member_router, tags=["Member Management"])
# app.include_router(member_admin_router, prefix="/api/v1/members", tags=["Member Admin"])

# Include Scheme and Commission Management routers
from services.routers import scheme_router, commission_router
app.include_router(scheme_router.router, prefix="/api/v1", tags=["Scheme Management"])
app.include_router(commission_router.router, prefix="/api/v1", tags=["Commission Management"])

from services.routers import kyc

app.include_router(kyc.router)

# Startup event
@app.on_event("startup")
async def startup():
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    # Close database connections
    engine.dispose()

# Initialize app state
async def close_sessions():
    """Close any active database sessions"""
    try:
        # For SQLAlchemy, we dispose the engine connection pool
        from database.database import engine
        engine.dispose()
    except Exception as e:
        logger.error(f"Error closing sessions: {str(e)}", exc_info=True)

app.state.close_sessions = close_sessions

# Mount static files last
app.mount("/static", StaticFiles(directory="static"), name="static")

# Startup event handler
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Bandru API...")
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Bandru API...")
    try:
        # Close database connections
        engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
        raise

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    try:
        # Test database connection
        with session_scope() as db:
            db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": app.version,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": app.version,
            "error": str(e)
        }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = ".".join([str(l) for l in error.get("loc", [])])
        msg = error.get("msg", "Invalid input")
        error_messages.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": error_messages
        }
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = ".".join([str(l) for l in error.get("loc", [])])
        msg = error.get("msg", "Invalid input")
        error_messages.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": error_messages
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        }
    }
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=log_config,
        log_level="info"
    )