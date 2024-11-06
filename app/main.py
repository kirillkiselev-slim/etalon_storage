from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends

from app.api.v1.endpoints import products, production_batches, warehouse, healthcheck
from app.core.models.db import sessionmanager, get_db, create_all_tables
from app.api.v1.api import api


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await create_all_tables()
    yield
    if sessionmanager._engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title='Storage', docs_url='/api/docs',
              redoc_url='/api/redoc')

api_start = ...

app.include_router(products)
# app.include_router()
# app.include_router()
# app.include_router()


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', reload=True, port=8000)
