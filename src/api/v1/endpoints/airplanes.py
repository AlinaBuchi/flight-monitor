from fastapi import APIRouter, HTTPException, Query
from database import MongoConnector
from bson.objectid import ObjectId
from models import Airplane
import math

airplanes_router = APIRouter(prefix="/planes", tags=["planes"])
connector = MongoConnector()


@airplanes_router.get("", tags=['planes'])
def get_items(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100)):
    skip = (page - 1) * per_page
    limit = per_page

    airplanes = connector.list_paginated("planes", skip=skip, limit=limit)
    airplanes_data = []
    for airplane in airplanes:
        airplane['_id'] = str(airplane['_id'])  # Convert _id to string
        if airplane.get("history") is not None:
            del airplane["history"]

        airplanes_data.append(airplane)

    total_items = connector.count("planes")
    total_pages = math.ceil(total_items / limit)
    current_page = math.ceil((skip + 1) / limit)
    metadata = {
        "total_items": total_items,
        "items_per_page": limit,
        "total_pages": total_pages,
        "current_page": current_page
    }

    return {"metadata": metadata, "items": airplanes_data}


@airplanes_router.get("/{plane_id}", tags=['planes'])
def get_item(plane_id: str):
    airplane = connector.read("planes", plane_id)
    if airplane is None:
        return HTTPException(status_code=404, detail="Airplane not found")

    airplane['_id'] = str(airplane['_id'])  # Convert _id to string
    if airplane.get("history") is not None:
        del airplane["history"]

    return airplane


@airplanes_router.put("/{plane_id}", tags=['planes'])
def update_item(plane_id: str, item: Airplane):
    airplane = connector.read("planes", plane_id)
    if airplane is None:
        return HTTPException(status_code=404, detail="Airplane not found")

    result = connector.update_one("planes", {"_id": ObjectId(plane_id)}, item.dict())

    return result


@airplanes_router.post("", tags=['planes'])
def save_item(item: Airplane):
    plane_id = connector.insert_one("planes", item.dict())

    return str(plane_id)


@airplanes_router.delete("/{plane_id}", tags=['planes'])
def delete_item(plane_id: str):
    airplane = connector.read("planes", plane_id)
    if airplane is None:
        return HTTPException(status_code=404, detail="Airplane not found")

    result = connector.delete_one("planes", {"_id": ObjectId(plane_id)})

    return result


@airplanes_router.get("/{plane_id}/history", tags=['planes'])
def get_item_history(plane_id: str):
    airplane = connector.read("planes", plane_id)
    if airplane is None:
        return HTTPException(status_code=404, detail="Airplane not found")

    history = airplane.get("history")
    if history is None:
        return HTTPException(status_code=404, detail="Airplane history not found")

    history_json = [
        {
            "event": item["event"],
            "gate": {
                "$ref": item["gate"].collection,
                "$id": str(item["gate"].id)
            },
            "runway": {
                "$ref": item["runway"].collection,
                "$id": str(item["runway"].id)
            }
        }
        for item in history
    ]

    return history_json
