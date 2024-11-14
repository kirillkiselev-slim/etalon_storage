from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.v1.endpoints import products, production_batches, warehouse, healthcheck
from core.models.db import sessionmanager, create_all_tables
from api.v1 import api


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await create_all_tables()
    yield
    if sessionmanager._engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title='Storage', docs_url='/api/docs',
              redoc_url='/api/redoc')

api_start = api

app.include_router(products)
app.include_router(production_batches)
app.include_router(warehouse)
# app.include_router()


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', reload=True, port=8001)
