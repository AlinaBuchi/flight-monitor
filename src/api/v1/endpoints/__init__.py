from fastapi import APIRouter
from .airplanes import airplanes_router

api_endpoints = APIRouter()
api_endpoints.include_router(airplanes_router)
