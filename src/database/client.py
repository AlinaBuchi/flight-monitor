from pymongo import MongoClient
from pymongo.collection import Collection
from typing import List, Any
from bson.objectid import ObjectId


from .base import Singleton, StorageObject


class MongoConnector(Singleton, StorageObject):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # for docker usage:
            cls._instance.client = MongoClient("mongodb://database:27017")
            # for other cases:
            # cls._instance.client = MongoClient("mongodb://localhost:27017:27017")
            cls._instance.planes_collection = cls._instance.client["flight_monitor"]["planes"]
            cls._instance.gates_collection = cls._instance.client["flight_monitor"]["gates"]
            cls._instance.runways_collection = cls._instance.client["flight_monitor"]["runways"]
        return cls._instance

    def select_collection(self, collection_name: str) -> Collection:
        if collection_name == "planes":
            return self.planes_collection
        elif collection_name == "gates":
            return self.gates_collection
        elif collection_name == "runways":
            return self.runways_collection
        else:
            raise ValueError("Invalid collection name")

    def insert_one(self, collection_name: str, document: dict) -> Any:
        collection = self.select_collection(collection_name)
        result = collection.insert_one(document)

        return result.inserted_id

    def insert_many(self, collection_name: str, documents: List[dict]) -> None:
        collection = self.select_collection(collection_name)
        collection.insert_many(documents)

    def read(self, collection_name: str, item_id: str) -> dict:
        collection = self.select_collection(collection_name)
        result = collection.find_one({"_id": ObjectId(item_id)})

        return result

    def list(self, collection_name: str, search_params: dict = None) -> List[dict]:
        collection = self.select_collection(collection_name)
        result = collection.find(search_params)
        items = list(result)

        return items

    def list_paginated(self, collection_name: str, skip: int = 0, limit: int = 10) -> List[dict]:
        collection = self.select_collection(collection_name)
        result = collection.find().skip(skip).limit(limit)
        items = list(result)

        return items

    def count(self, collection_name: str):
        collection = self.select_collection(collection_name)

        return collection.count_documents({})

    def update_one(self, collection_name: str, search_params: dict, to_update: dict) -> dict[str, Any]:
        collection = self.select_collection(collection_name)
        result = collection.update_one(search_params, {'$set': to_update})

        return result.raw_result

    def delete_one(self, collection_name: str, search_params: dict) -> dict[str, Any]:
        collection = self.select_collection(collection_name)
        result = collection.delete_one(search_params)

        return result.raw_result

    def get_id(self, collection_name: str, params: dict) -> None | str:
        collection = self.select_collection(collection_name)
        obj = collection.find_one(params)
        if obj:
            return str(obj["_id"])
        else:
            return None

    def update_history(self, collection_name: str, plane_id: int, update_dict: dict) -> None:
        collection = self.select_collection(collection_name)
        collection.update_one({'airplane_id': plane_id}, {'$push': {'history': {'$each': [update_dict]}}})

