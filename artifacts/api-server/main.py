import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis, reports

app = FastAPI(
    title="QAID API",
    description="AI-powered Financial Risk, Fraud Detection & IFRS Compliance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/healthz")
def health_check():
    return {"status": "ok"}


app.include_router(analysis.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
