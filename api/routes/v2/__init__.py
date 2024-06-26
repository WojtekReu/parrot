from importlib import import_module
from fastapi import APIRouter


router = APIRouter(prefix="/v2")
routes = (
    "auth",
    "book",
    "flashcard",
    "sentence",
    "user",
    "word",
    "dictionary",
)

for module_name in routes:
    api_module = import_module(f"api.routes.v2.{module_name}")
    api_module_router = api_module.router
    router.include_router(api_module_router)
