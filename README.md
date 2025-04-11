# news_api

news_api/
│
├── app/
│   ├── __init__.py
│   ├── main.py             ← FastAPI 엔트리포인트
│   ├── routes/
│   │   ├── __init__.py
│   │   └── news.py         ← /news/summarize API 정의
│   ├── services/
│   │   ├── __init__.py
│   │   └── news_collector.py  ← 네이버 뉴스 수집 및 요약 함수
│   ├── utils/
│   │   ├── __init__.py
│   │   └── driver.py       ← Selenium 관련 도구 (드라이버 생성 등)
│   └── prompts/
│       └── news_summary_prompt.txt  ← 프롬프트 파일 따로 관리
│
├── requirements.txt
├── Dockerfile
└── README.md

