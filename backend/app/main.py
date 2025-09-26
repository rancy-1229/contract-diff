from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents, comparisons, ai_review

app = FastAPI(title="合同差异对比系统", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/images", StaticFiles(directory="uploads/images"), name="images")
app.mount("/documents", StaticFiles(directory="uploads/documents"), name="documents")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 注册路由
app.include_router(documents.router)
app.include_router(comparisons.router)
app.include_router(ai_review.router)

@app.get("/")
async def root():
    return {"message": "合同差异对比系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
