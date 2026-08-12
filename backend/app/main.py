from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.buildings import router as buildings_router
from app.api.v1.routes.floors import router as floors_router
from app.api.v1.routes.locations import router as locations_router
from app.api.v1.routes.department_locations import router as department_locations_router
from app.api.v1.routes.departments import router as departments_router

from app.config.settings import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Biomedical Asset Management System Backend",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(buildings_router)
app.include_router(floors_router)
app.include_router(locations_router)
app.include_router(department_locations_router)
app.include_router(departments_router)

@app.get("/")
def root():
    return {"message": "Welcome to the BAMS API"}


@app.get("/health")
def health():
    return {"status": "ok"}