from fastapi import APIRouter

products = APIRouter(
    prefix='/api/v1/products',
    tags=['products'],
    responses={404: {'description': 'Not found'}},
)

production_batches = APIRouter(
    prefix='/api/v1/production/batches',
    tags=['production_batches'],
    responses={404: {'description': 'Not found'}},
)

warehouse = APIRouter(
    prefix='/api/v1/warehouse',
    tags=['warehouse'],
    responses={404: {'description': 'Not found'}},
)

healthcheck = APIRouter(
    prefix='/api/v1/healthcheck',
    tags=['healthcheck'],
    responses={404: {'description': 'Not found'}},
)