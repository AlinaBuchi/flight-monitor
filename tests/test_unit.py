from datetime import datetime

from src.airport import Airport
from src.models.airplane import (
    AirplaneInternationalFlight,
    AirplaneDomesticFlight
)

import pytest


@pytest.fixture()
def my_airport():
    return Airport('Springvale')


@pytest.fixture()
def domestic_plane():
    return AirplaneDomesticFlight(
        airplane_id=123456,
        model='Airbus 123',
        reason='destination',
        flight_time=datetime(2023, 3, 7, 13, 00),
        origin='Wintervale',
        destination='Springvale'
    )


@pytest.fixture()
def international_plane():
    return AirplaneInternationalFlight(
        airplane_id=1234,
        model='Airbus 123',
        reason='destination',
        flight_time=datetime(2023, 3, 7, 7, 00),
        origin='Singapore',
        destination='Springvale'
    )


@pytest.fixture()
def repair_plane_1():
    return AirplaneDomesticFlight(
        airplane_id=1456,
        model='Airbus 123',
        reason='repair',
        flight_time=datetime(2023, 3, 7, 13, 00),
        origin='Autumnville',
        destination='Springvale'
    )


@pytest.fixture()
def repair_plane_2():
    return AirplaneInternationalFlight(
        airplane_id=166478,
        model='Airbus 123',
        reason='repair',
        flight_time=datetime(2023, 3, 7, 13, 20),
        origin='Singapore',
        destination='Springvale'
    )


def test_gate_allocation_domestic(my_airport, domestic_plane):
    gate_number = my_airport.gate_allocation(domestic_plane)
    assert my_airport.airport_gates[gate_number].is_occupied is True
    assert gate_number in range(1, 4)


def test_gate_allocation_international(my_airport, international_plane):
    gate_number = my_airport.gate_allocation(international_plane)
    assert my_airport.airport_gates[gate_number].is_occupied is True
    assert gate_number == 4


def test_free_up_gate(my_airport, domestic_plane):
    gate_number = my_airport.gate_allocation(domestic_plane)
    my_airport.free_up_gate(gate_number)
    assert my_airport.airport_gates[gate_number].is_occupied is False


def test_runway_allocation_free(my_airport, domestic_plane):
    runway_number = my_airport.runway_allocation()
    assert runway_number in [1, 2]
    assert my_airport.runways[runway_number].get_occupied() is True


def test_runway_allocation_occupied(my_airport, domestic_plane):
    my_airport.runways[1].set_occupied(True)
    my_airport.runways[2].set_occupied(True)
    assert my_airport.runways[1].get_occupied() is True
    assert my_airport.runways[2].get_occupied() is True
    runway_number = my_airport.runway_allocation()
    assert runway_number is None


def test_check_hangar_status(my_airport, repair_plane_1, repair_plane_2):
    hangar = my_airport.hangar
    my_airport.check_hangar(datetime(2023, 3, 7, 13, 00), 3, repair_plane_1)
    assert hangar.is_occupied is True
    assert hangar.end_date == datetime(2023, 3, 10, 13, 00)
    my_airport.check_hangar(datetime(2023, 3, 7, 7, 00), 3, repair_plane_2)
    assert len(my_airport.awaiting_repairs) == 1
    hangar.set_free()
    assert hangar.is_occupied is False
