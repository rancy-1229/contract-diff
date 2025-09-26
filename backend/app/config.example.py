import os
from typing import Optional

class Settings:
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/contract_diff")
    
    # 文件存储配置
    UPLOAD_DIR: str = "uploads"
    DOCUMENTS_DIR: str = "uploads/documents"
    IMAGES_DIR: str = "uploads/images"
    TEMP_DIR: str = "uploads/temp"
    
    # 文件大小限制 (50MB)
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    
    # 支持的文件类型
    ALLOWED_FILE_TYPES: list = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # 支持的文件扩展名
    ALLOWED_EXTENSIONS: list = [".pdf", ".docx", ".doc"]
    
    # AI模型配置
    ARK_BASE_URL: str = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3/")
    ARK_API_KEY: str = os.getenv("ARK_API_KEY", "your_api_key_here")
    ARK_MODEL: str = os.getenv("ARK_MODEL", "doubao-seed-1-6-flash-250828")

settings = Settings()
