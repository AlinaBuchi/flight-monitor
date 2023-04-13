

class Gate:
    def __init__(self, number: int, gate_type: str) -> None:
        self.number: int = number
        self.gate_type: str = gate_type
        self.is_occupied: bool = False

    def set_occupied(self, is_occupied) -> None:
        self.is_occupied = is_occupied

    def get_occupied(self) -> bool:
        return self.is_occupied

    def __str__(self) -> str:
        return (
            f'Gate Number -> {self.number}, '
            f'Gate Type -> {self.gate_type}, '
            f'Gate Status -> {self.is_occupied}, '
        )
