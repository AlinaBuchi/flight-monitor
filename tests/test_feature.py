# import built-in modules
from datetime import datetime
import os

# import third party modules
import pytest

# import from local apps
from src.airport import Airport
from src.models.airplane import (
    AirplaneInternationalFlight,
    AirplaneDomesticFlight
)


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
    return AirplaneDomesticFlight(
        airplane_id=166478,
        model='Airbus 123',
        reason='repair',
        flight_time=datetime(2023, 3, 7, 13, 20),
        origin='Wintervale',
        destination='Springvale'
    )


@pytest.fixture()
def my_airport():
    return Airport('Springvale')


def test_arrival_depart_domestic(my_airport, domestic_plane):
    my_airport.arrive_plane(domestic_plane)
    assert len(my_airport.arrivals) == 1
    assert my_airport.awaiting_departure.qsize() == 1
    assert domestic_plane.gate_number in [1, 2, 3]
    assert my_airport.airport_gates[domestic_plane.gate_number].get_occupied() is True

    my_airport.depart_plane(domestic_plane, 3)
    assert domestic_plane.departure_time == datetime(2023, 3, 7, 13, 0, 3)
    assert my_airport.airport_gates[domestic_plane.gate_number].get_occupied() is False
    assert len(my_airport.departures) == 1
    assert domestic_plane.destination == 'Wintervale'


def test_arrival_depart_international(my_airport, international_plane):
    my_airport.arrive_plane(international_plane)
    assert len(my_airport.arrivals) == 1
    assert my_airport.awaiting_departure.qsize() == 1
    assert international_plane.gate_number == 4
    assert my_airport.airport_gates[international_plane.gate_number].get_occupied() is True

    my_airport.depart_plane(international_plane, 3)
    assert international_plane.departure_time == datetime(2023, 3, 8, 21, 0, 3)
    assert my_airport.airport_gates[international_plane.gate_number].get_occupied() is False
    assert len(my_airport.departures) == 1
    assert international_plane.destination == 'Singapore'


def test_arrival_repair(my_airport, repair_plane_1):
    my_airport.arrive_plane(repair_plane_1)
    assert len(my_airport.arrivals) == 1
    assert my_airport.awaiting_departure.qsize() == 0
    assert my_airport.hangar.plane_id == repair_plane_1.airplane_id


def test_arrival_multiple_repairs(my_airport, repair_plane_1, repair_plane_2):
    my_airport.arrive_plane(repair_plane_1)
    my_airport.arrive_plane(repair_plane_1)
    assert len(my_airport.arrivals) == 2
    assert my_airport.awaiting_departure.qsize() == 0
    assert my_airport.hangar.plane_id == repair_plane_1.airplane_id
    assert len(my_airport.awaiting_repairs) == 1


def test_arrival_gates_occupied(my_airport, international_plane):
    my_airport.airport_gates[4].set_occupied(True)
    try:
        my_airport.arrive_plane(international_plane)
        assert False, 'Cannot land. Gate occupied'
    except Exception:
        assert True


def test_arrival_runways_occupied(my_airport, international_plane):
    my_airport.runways[1].set_occupied(True)
    my_airport.runways[2].set_occupied(True)
    try:
        my_airport.arrive_plane(international_plane)
        assert False, 'Cannot land. Runways occupied'
    except Exception:
        assert True


def test_export_fail(my_airport):
    with pytest.raises(Exception):
        my_airport.export_arrivals(1)
    with pytest.raises(Exception):
        my_airport.export_departures(1)


def test_export_arrivals_success(my_airport, international_plane, domestic_plane):
    my_airport.arrivals = [international_plane, domestic_plane]
    my_airport.export_arrivals()
    assert os.path.exists('arrivals.json') is True


def test_export_departures_success(my_airport, international_plane, domestic_plane):
    my_airport.departures = [international_plane, domestic_plane]
    my_airport.export_departures()
    assert os.path.exists('departures.json') is True
