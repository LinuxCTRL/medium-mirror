from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import router as api_router
from app.core.config import settings
from app.core.database import engine, Base

app = FastAPI(title=settings.PROJECT_NAME)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

# We include the router at root because it now contains the HTML views at / and /v/{id}
# The API endpoints are also included here
app.include_router(api_router)
