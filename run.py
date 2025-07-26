import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 获取端口，如果环境变量中没有设置，则使用默认值8000
    port = int(os.getenv("PORT", 8000))
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # 开发模式下启用热重载
        log_level="info"
    )
    
    print(f"服务器已启动，访问 http://localhost:{port}")