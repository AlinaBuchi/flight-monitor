

class Runway:
    def __init__(self, number: int) -> None:
        self.number: int = number
        self.is_occupied: bool = False

    def set_occupied(self, is_occupied) -> None:
        self.is_occupied = is_occupied

    def get_occupied(self) -> bool:
        return self.is_occupied
