from datetime import datetime, timedelta
from typing import Type


class Hangar:
    def __init__(self) -> None:
        self.is_occupied: bool = False
        self.start_date: datetime = Type[datetime]
        self.end_date: datetime = Type[datetime]
        self.plane_id: int = Type[int]

    def set_occupied(self, start_date: datetime, number_of_days: int, plane_id: int) -> None:
        self.is_occupied = True
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=number_of_days)
        self.plane_id = plane_id

    def set_free(self) -> None:
        self.is_occupied = False
        self.start_date = None
        self.end_date = None
        self.plane_id = None

    def __str__(self) -> str:
        return (
            f'Aiplane ID -> {self.plane_id}, '
            f'Repairs start on -> {self.start_date}, '
            f'Repairs end on  -> {self.end_date} '
        )
