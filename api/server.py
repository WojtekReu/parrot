from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from .routes import router as api_router
from wing.config import settings
from wing.models import *


origins = [
    ("https://" if settings.SSL_ENABLED else "http://")
    + settings.PROJECT_DOMAIN
    + (f":{settings.PROJECT_DOMAIN_PORT}" if settings.PROJECT_DOMAIN_PORT else "")
]


def get_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/docs",
    )
    app.include_router(api_router, prefix="/api")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    add_pagination(app)
    return app


app = get_application()


@app.get("/", tags=["health"])
async def health():
    return dict(
        name=settings.PROJECT_NAME,
        version=settings.VERSION,
        status="OK",
        message="Visit /docs for more information.",
    )
