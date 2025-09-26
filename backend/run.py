import uvicorn
import os

if __name__ == "__main__":
    # 确保上传目录存在
    os.makedirs("uploads/documents/standard", exist_ok=True)
    os.makedirs("uploads/documents/target", exist_ok=True)
    os.makedirs("uploads/images", exist_ok=True)
    os.makedirs("uploads/temp", exist_ok=True)
    
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True
    )
