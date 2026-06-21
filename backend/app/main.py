from fastapi import FastAPI
from .api.routes import router as api_router

app = FastAPI(
    title="面向内容立项决策的剧本评估 Agent 系统 (骨架版)",
    description="影视/短剧立项辅助评估多 Agent 系统，支持剧本结构化解析、RAG 同类对比、Quality Review 修正及人设记忆。",
    version="1.0.0"
)

# 注册 API 路由
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
