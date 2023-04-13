from datetime import datetime
from pydantic import BaseModel


class Airplane(BaseModel):
    airplane_id: int
    model: str
    reason: str
    flight_time: datetime
    origin: str
    destination: str
    flight_type: str
    departure_time: datetime | None = None
    gate_number: int | None = None

