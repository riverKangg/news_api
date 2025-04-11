from fastapi import FastAPI
from app.routes.news import router as news_router

app = FastAPI(
    title="News Summary API",
    version="1.0.0"
)

app.include_router(news_router, prefix="/news")

