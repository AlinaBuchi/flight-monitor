# built-in imports
import copy
import time
import random as rnd
import json
from datetime import (
    datetime,
    timedelta,
    date
)
from queue import Queue
from threading import Lock

# local app imports
from models.hangar import Hangar
from models.gate import (
    Gate,
    DomesticGate,
    InternationalGate
)
from models.runway import Runway
from models.airplane import Airplane


class Airport:

    def __init__(self, name: str) -> None:
        self.name: str = name

        self.awaiting_departure = Queue()
        self.arrivals: list[Airplane] = []
        self.departures: list[Airplane] = []
        self.hangar: Hangar = Hangar()
        self.awaiting_repairs: list[Airplane] = []
        self.plane_queue = Queue()
        self.lock = Lock()

        self.runways: dict[int: Runway] = {
            1: Runway(1),
            2: Runway(2)
        }

        self.airport_gates: dict[int: Gate] = {
            1: DomesticGate(1),
            2: DomesticGate(2),
            3: DomesticGate(3),
            4: InternationalGate(4)
        }

    # return Runway.number or none if no runway available
    def runway_allocation(self) -> None | int:
        for runway in self.runways:
            time.sleep(2)
            status = self.runways[runway].get_occupied()
            if not status:
                self.lock.acquire()
                self.runways[runway].set_occupied(True)
                self.lock.release()
                print(f'Runway {runway} is free and has been allocated to plane')
                return self.runways[runway].number
            else:
                print(f'Runway {runway} not available.')
                return None

    # returns gate number if available, else -> none
    def gate_allocation(self, plane: Airplane) -> None | int:
        if plane.flight_type == 'Domestic':
            # get all gates that are domestic and free
            free_dom_gates = {k: v for k, v in self.airport_gates.items() if
                              v.get_occupied() is not True and isinstance(v, DomesticGate)}
            if not free_dom_gates:
                print('No domestic gates free.')
                return None
            else:
                chosen_gate = list(free_dom_gates.keys())[0]
                self.lock.acquire()
                free_dom_gates[chosen_gate].set_occupied(True)
                self.lock.release()
                print(f'Domestic gate {chosen_gate} has been allocated to {plane.airplane_id}')
                return chosen_gate
        elif plane.flight_type == 'International':
            # get all gates that are international and free --> for future use.
            # In the case of the project we only have gate 4 as intl
            free_intl_gates = {
                k: v for k, v in self.airport_gates.items() if v.get_occupied() is not True and isinstance(v, InternationalGate)
            }
            if not free_intl_gates:
                print('No international gates free.')
                return None
            else:
                chosen_gate = list(free_intl_gates.keys())[0]
                self.lock.acquire()
                free_intl_gates[chosen_gate].set_occupied(True)
                self.lock.release()
                print(f'International gate {chosen_gate} has been allocated to {plane.airplane_id}')
                return chosen_gate

    def free_up_gate(self, number: int) -> None:
        self.lock.acquire()
        self.airport_gates[number].set_occupied(False)
        self.lock.release()
        print(f'Gate {number} is now free.')

    def free_up_runway(self, number: int) -> None:
        self.lock.acquire()
        self.runways[number].set_occupied(False)
        self.lock.release()
        print(f'Runway {number} is now free.')

    # check if the hanger is free, if not, add to awaiting repairs
    def check_hangar(self, start_date: datetime, days: int, plane: Airplane) -> None:
        if not self.hangar.is_occupied:
            self.lock.acquire()
            self.hangar.set_occupied(start_date, days, plane.airplane_id)
            self.lock.release()
            print('\n', '-' * 10, 'AIRPLANE IN HANGER', '-' * 10, '\n')
            print('Plane with details ' 
                  f'{plane.airplane_id, plane.origin, datetime.strftime(plane.flight_time, "%Y-%M-%d %H:%M:%S")}' 
                  ' has been sent to Hangar for repairs.')
        else:
            self.awaiting_repairs.append(plane)
            print('\n', '-' * 10, 'NEW AIRPLANE WAITING FOR HANGAR', '-' * 10, '\n')
            print('Plane with details ' 
                  f'{plane.airplane_id, plane.origin, datetime.strftime(plane.flight_time, "%Y-%M-%d %H:%M:%S")}' 
                  ' is on the wait list to enter the Hangar for repairs.')
            print('The updated list is:')
            [print(plane) for plane in self.awaiting_repairs]
        print('\n', '-' * 10, 'HANGAR INFO - OCCUPIED BY', '-' * 10, '\n')
        print(f'Hangar occupied by: {self.hangar}')

    def arrive_plane(self, plane: Airplane) -> bool:
        """
        We need both a gate and a runway for landing.
        If we get only one of them, we need to free it, so we won't block the flow.
        For repairs:
        - we check the hangar
         - add the plane to the arrival list
         - free up gate and runway
        For normal planes - free up runway only, as the gate remains blocked for the plane until take-off.
        * using deepcopy because data gets overwritten for departure.
        """
        print('*' * 10, 'ARRIVAL DETAILS' + '*' * 10)
        gate_number = self.gate_allocation(plane)
        runway_number = self.runway_allocation()

        if gate_number is None or runway_number is None:
            if gate_number is not None:
                self.free_up_gate(gate_number)
            if runway_number is not None:
                self.free_up_runway(runway_number)
            return False

        if plane.reason == 'repair':
            self.check_hangar(plane.flight_time, rnd.randint(2, 5), plane)
            self.arrivals.append(copy.deepcopy(plane))

            self.free_up_gate(gate_number)
            self.free_up_runway(runway_number)

        else:
            self.arrivals.append(copy.deepcopy(plane))
            plane.gate_number = gate_number
            self.awaiting_departure.put(copy.deepcopy(plane))

            print('\n', '-' * 10, 'NEW ARRIVALS', '-' * 10, '\n')
            print(f'Plane with details {plane.airplane_id, plane.origin, datetime.strftime(plane.flight_time, "%Y-%M-%d %H:%M:%S")},')
            print(f'Gate -> {gate_number}, Runway -> {runway_number} has landed successfully.')
            self.free_up_runway(runway_number)
        return True

    def depart_plane(self, plane: Airplane, hours_takeoff: int) -> bool:
        """
        The plane is already blocking a gate from arrival.
        When taking off, we invert the origin with the destination, except for connection flights.
        We pass the parameter hours_takeoff used for calculating departure time, but set it to sec for simulation.
        International flights - special timetable.
        Find a free runway, add to departure list and free both runway and gate.
        """
        if plane.destination == 'Springvale':
            plane.destination, plane.origin = plane.origin, plane.destination
        if plane.flight_type == 'Domestic':
            time.sleep(hours_takeoff)
            plane.departure_time = plane.flight_time + timedelta(seconds=hours_takeoff)
        elif plane.flight_type == 'International':
            time.sleep(3)
            if plane.flight_time == datetime(2023, 3, 7, 7, 00):
                plane.departure_time = datetime(2023, 3, 7, 21, 00) + timedelta(days=1, seconds=hours_takeoff)
            else:
                plane.departure_time = datetime(2023, 3, 7, 7, 00) + timedelta(days=1, seconds=hours_takeoff)

            print('*' * 10, 'DEPARTURE DETAILS', '*' * 10)

        runway_number = self.runway_allocation()
        if runway_number is None:
            return False

        self.departures.append(plane)
        print('\n', '-' * 10, 'NEW DEPARTURES', '-' * 10, '\n')
        print(f'Plane with details ' 
              f'{plane.airplane_id, plane.destination, datetime.strftime(plane.departure_time, "%Y-%M-%d %H:%M:%S")}' 
              f', Runway -> {runway_number} has taken off successfully')

        self.free_up_gate(plane.gate_number)
        self.free_up_runway(runway_number)
        return True

    @staticmethod
    def default(datetime_obj: datetime) -> str:
        """
       serializing datetime to str for json
        """
        if isinstance(datetime_obj, (date, datetime)):
            return datetime_obj.isoformat()

    def export_arrivals(self) -> None:
        try:
            with open('arrivals.json', 'w') as f:
                plane_arrivals = []
                for plane in self.arrivals:
                    plane_arrivals.append(plane.dict())
                json.dump(plane_arrivals, f, indent=4, default=self.default)
        except Exception as e:
            print('Something went wrong and the export of arrivals failed: ', e)

    def export_departures(self) -> None:
        try:
            with open('departures.json', 'w') as f:
                plane_departures = []
                for plane in self.departures:
                    plane_departures.append(plane.dict())
                json.dump(plane_departures, f, indent=4, default=self.default)
        except Exception as e:
            print('Something went wrong and the export of departures failed: ', e)
