from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from wall_engine.api.routes import design_route

app = FastAPI(
    title="CCP-14 Wall Design API",
    description="API for designing cantilever retaining walls according to CCP-14 / AASHTO LRFD.",
    version="1.0.0"
)

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(design_route.router, prefix="/api/v1/design", tags=["Design"])

@app.get("/")
def root():
    return {"message": "Welcome to the CCP-14 Wall Engine API. Go to /docs for Swagger UI."}

@app.get("/health")
def health():
    return {"status": "ok"}
