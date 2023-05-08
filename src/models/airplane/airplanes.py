from .base import Airplane


class AirplaneDomesticFlight(Airplane):
    destination = 'Springvale'
    flight_type = 'Domestic'


class AirplaneInternationalFlight(Airplane):
    flight_type = 'International'
