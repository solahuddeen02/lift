from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import auth_routes
from app.core.config import settings
from app.core.database import Base, engine
from app.modules.categories import routes as category_routes
from app.modules.dashboard import routes as dashboard_routes
from app.modules.journal import routes as journal_routes
from app.modules.routines import routes as routine_routes
from app.modules.tasks import routes as task_routes

# dev: create tables ตรงๆ — ตอน merge เข้า Atlas ค่อยเปลี่ยนเป็น Alembic
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(task_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(routine_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(category_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(journal_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_routes.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
