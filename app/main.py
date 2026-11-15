from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="To-Do API",
    description="API REST de gerenciamento de tarefas",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
