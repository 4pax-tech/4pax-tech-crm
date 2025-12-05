from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import contacts, interactions, proposals, actions

app = FastAPI(title="CRM API", description="Freelancer CRM API", version="0.1.0")

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contacts.router, prefix="/api")
app.include_router(interactions.router, prefix="/api")
app.include_router(proposals.router, prefix="/api")
app.include_router(actions.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "CRM API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
