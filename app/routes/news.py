from fastapi import APIRouter, Query
from app.services.news_collector import collect_and_summarize_news

router = APIRouter()

@router.get("/summarize")
def summarize_news(
    query: str = Query(..., description="검색 키워드"),
    category: str = Query(..., description="카테고리 (예: 당사, 경쟁사 등)")
):
    result = collect_and_summarize_news(query, category)
    return {"status": "success", "data": result}

