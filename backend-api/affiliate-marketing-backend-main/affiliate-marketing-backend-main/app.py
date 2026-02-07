from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from services.routers import router as chat_router
from services import products_service
from services import comparison_service
from utils.db import insert_json_to_mongo
from utils.logger import log_api_request, log_api_error, setup_logging
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logger = setup_logging()

print("Email user is:", os.getenv("EMAIL_USER"))



origins = ["*"]

app = FastAPI(
    title="Affiliate Marketing API",
    description="Complete affiliate marketing platform API with multi-vendor product comparison",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        log_api_request(
            endpoint=str(request.url),
            params=dict(request.query_params),
            user_ip=client_ip
        )
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        log_api_error(
            endpoint=str(request.url),
            error=e,
            params=dict(request.query_params)
        )
        raise

@app.get("/ping")
async def ping():
    return {"res": True}

app.include_router(chat_router)
app.include_router(products_service.router)
app.include_router(comparison_service.router)


# Insert single JSON file into MongoDB on startup
@app.on_event("startup")
async def load_data_into_mongo():
    db_name = "ecommerce"
    collection_name = "ecommerce_data"
    json_path = "extra_files\productlisting.json"

    if os.path.exists(json_path):
        try:
            await insert_json_to_mongo(json_path,db_name,collection_name)
            print(f" Data inserted from {json_path} into collection '{collection_name}'")
        except Exception as e:
            print(f" Failed to insert {json_path}: {e}")
    else:
        print(f"File not found: {json_path}")