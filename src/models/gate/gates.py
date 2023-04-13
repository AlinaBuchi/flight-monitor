from .base import Gate


class DomesticGate(Gate):
    def __init__(self, number) -> None:
        super().__init__(number, 'Domestic')


class InternationalGate(Gate):
    def __init__(self, number) -> None:
        super().__init__(number, 'International')
