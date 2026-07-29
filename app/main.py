"""
定义FastAPI的app对象，注册路由，挂载静态文件等
"""
from fastapi import FastAPI
from app.routers import router 
from app.config.config import get_setting
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """
    构建app，注册routers，挂载静态文件，写一个简单的 健康检查的接口
    """

    app = FastAPI()

    setting = get_setting()

    app.include_router(router=router,prefix=setting.api_prefix)

    app.mount("/",StaticFiles(directory="static",html=True),name="static")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    @app.get("/health")
    def get_app_health():

        return {"status":"ok"}

    return app


app = create_app()


