import uvicorn
from app.config.settings import settings
from app.web.app import create_web_app

app = create_web_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.web_main:app",
        host=settings.WEB_ADMIN_HOST,
        port=settings.WEB_ADMIN_PORT,
        reload=False
    )
