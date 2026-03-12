# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.domains.chat.router import router as chat_router

# الطريقة الحديثة في FastAPI (Lifespan) لتهيئة قاعدة البيانات عند تشغيل السيرفر
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables asynchronously if they don't exist in PostgreSQL
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield # هنا السيرفر راهو شاعل ويخدم
    
    # Shutdown logic can go here (مثلا غلق الاتصال بقاعدة البيانات عند إطفاء السيرفر)
    await engine.dispose()

app = FastAPI(
    title="Student Environment API",
    description="Backend for University Students App",
    version="1.0.0",
    lifespan=lifespan # ربطنا الـ lifespan بالـ app
)

# CORS Middleware (ضرورية جدا باش تطبيق Flutter يقدر يتصل بالسيرفر بلا مشاكل)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # في الـ Production يُفضل تحط الـ Domains المسموحة فقط
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat_router)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "Online",
        "message": "Welcome to Student Environment API. Chat system is ready!"
    }