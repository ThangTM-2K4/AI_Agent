from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import public_router, router as report_router
from app.core.config import settings
from app.core.database import Base, engine

# Tạo bảng nếu chưa tồn tại (không xóa dữ liệu hiện có)
Base.metadata.create_all(engine)

app = FastAPI(title=settings.app_name)
app.include_router(report_router)
app.include_router(public_router)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.state.data_loaded = False

base_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=base_dir / "static"), name="static")
templates = Jinja2Templates(directory=str(base_dir / "templates"))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "data_loaded": bool(getattr(request.app.state, "data_loaded", False)),
            "user": request.session.get("user"),
        },
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
