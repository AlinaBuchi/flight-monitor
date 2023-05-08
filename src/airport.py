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
from bson.objectid import ObjectId

# local app imports

from models import (Hangar, InternationalGate, DomesticGate, Runway, Airplane)
from database import MongoConnector


class Airport:

    def __init__(self, name: str) -> None:
        self.name: str = name

        self.hangar: Hangar = Hangar()

        self.arrivals: list[Airplane] = []
        self.departures: list[Airplane] = []
        self.awaiting_repairs: list[Airplane] = []

        self.arrivals_queue = Queue()
        self.departures_queue = Queue()

        self.lock = Lock()
        self.connector = MongoConnector()

        runways_data = self.connector.read("runways")
        # initialize Runway objects with data from DB
        self.runways = [Runway(runway_data["number"]) for runway_data in runways_data]

        gates_data = self.connector.read("gates")
        self.gates = []
        # initialize Gate objects with data from DB
        for gate in gates_data:
            gate_number = gate["number"]
            gate_type = gate["gate_type"]
            if gate_type == "Domestic":
                self.gates.append(DomesticGate(gate_number))
            elif gate_type == "International":
                self.gates.append(InternationalGate(gate_number))

    def runway_allocation(self) -> None | int:
        while True:
            for runway in self.runways:
                time.sleep(2)
                status = runway.get_occupied()
                # if status is False, we occupy the runway and update the status in the DB
                if not status:
                    self.lock.acquire()
                    runway.set_occupied(True)
                    runway_to_change = {"number": runway.number}
                    new_runway_status = {"is_occupied": True}
                    self.connector.update_one("runways", runway_to_change, new_runway_status)
                    self.lock.release()
                    print(f'Runway {runway.number} is free and has been allocated to plane')
                    return runway.number
                else:
                    print(f'Runway {runway.number} not available.')
                    continue

    def gate_allocation(self, plane: Airplane) -> None | int:
        while True:
            if plane.flight_type == 'Domestic':
                # get all gates that are domestic and free
                # get the first gate free, occupy it and update the status
                free_dom_gates = [gate for gate in self.gates if
                                  gate.get_occupied() is not True and isinstance(gate, DomesticGate)]
                if not free_dom_gates:
                    print('No domestic gates free.')
                    continue
                else:
                    chosen_gate = free_dom_gates[0]
                    self.lock.acquire()
                    chosen_gate.set_occupied(True)
                    plane.gate_number = chosen_gate.number

                    gate_to_change = {"number": chosen_gate.number}
                    new_gate_status = {"is_occupied": True}
                    self.connector.update_one("gates", gate_to_change, new_gate_status)

                    self.lock.release()
                    print(f'Domestic gate {chosen_gate.number} has been allocated to {plane.airplane_id}')
                    return chosen_gate.number
            elif plane.flight_type == 'International':
                time.sleep(5)
                # get all gates that are international and free --> for future use.
                # In the case of the project we only have gate 4 as intl
                # get the first gate free, occupy it and update the status
                free_intl_gates = [gate for gate in self.gates if gate.get_occupied() is not True and isinstance(gate, InternationalGate)]
                if not free_intl_gates:
                    print('No international gates free.')
                    continue

                chosen_gate = free_intl_gates[0]
                self.lock.acquire()
                chosen_gate.set_occupied(True)
                plane.gate_number = chosen_gate.number

                gate_to_change = {"number": chosen_gate.number}
                new_gate_status = {"is_occupied": True}
                self.connector.update_one("gates", gate_to_change, new_gate_status)

                self.lock.release()
                print(f'International gate {chosen_gate.number} has been allocated to {plane.airplane_id}')
                return chosen_gate.number

    def free_up_gate(self, number: int) -> None:
        self.lock.acquire()

        gate_to_free = None
        for gate in self.gates:
            if gate.number == number:
                gate_to_free = gate

        gate_to_free.set_occupied(False)

        gate_to_change = {"number": gate_to_free.number}
        new_gate_status = {"is_occupied": False}
        self.connector.update_one("gates", gate_to_change, new_gate_status)

        self.lock.release()
        print(f'Gate {number} is now free.')

    def free_up_runway(self, number: int) -> None:
        self.lock.acquire()
        runway_to_free = None
        for runway in self.runways:
            if runway.number == number:
                runway_to_free = runway

        runway_to_free.set_occupied(False)
        runway_to_change = {"number": runway_to_free.number}
        new_runway_status = {"is_occupied": False}
        self.connector.update_one("runways", runway_to_change, new_runway_status)
        self.lock.release()
        print(f'Runway {number} is now free.')

    # check if the hanger is free, if not, add to awaiting repairs list
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

    def arrive_plane(self, plane: Airplane) -> None:
        """
        We need both a gate and a runway for landing.
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

        if plane.reason == 'repair':
            self.check_hangar(plane.flight_time, rnd.randint(2, 5), plane)
            self.arrivals.append(copy.deepcopy(plane))

            self.free_up_gate(gate_number)
            self.free_up_runway(runway_number)

        else:
            self.arrivals.append(copy.deepcopy(plane))

            plane.gate_number = gate_number
            self.departures_queue.put(copy.deepcopy(plane))

            print('\n', '-' * 10, 'NEW ARRIVALS', '-' * 10, '\n')
            print(f'Plane with details {plane.airplane_id, plane.origin, datetime.strftime(plane.flight_time, "%Y-%M-%d %H:%M:%S")},')
            print(f'Gate -> {gate_number}, Runway -> {runway_number} has landed successfully.')
            self.free_up_runway(runway_number)

        # get the id from the DB
        gate_id = ObjectId(self.connector.get_id("gates", {"number": gate_number}))
        runway_id = ObjectId(self.connector.get_id("runways", {"number": runway_number}))

        # update the history key in the DB with external references
        plane_history = {}
        plane_history.update({"event": "arrival"})
        plane_history.update({"gate": {"$ref": "gates", "$id": gate_id}})
        plane_history.update({"runway": {"$ref": "runways", "$id": runway_id}})

        self.connector.update_history("planes", plane.airplane_id, plane_history)

    def depart_plane(self, plane: Airplane, hours_takeoff: int) -> None:
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

        self.departures.append(plane)

        print('\n', '-' * 10, 'NEW DEPARTURES', '-' * 10, '\n')
        print(f'Plane with details ' 
              f'{plane.airplane_id, plane.destination, datetime.strftime(plane.departure_time, "%Y-%M-%d %H:%M:%S")}' 
              f', Runway -> {runway_number} has taken off successfully')

        self.free_up_gate(plane.gate_number)
        self.free_up_runway(runway_number)

        # get the id from the DB
        gate_id = ObjectId(self.connector.get_id("gates", {"number": plane.gate_number}))
        runway_id = ObjectId(self.connector.get_id("runways", {"number": runway_number}))

        # update the history key in the DB with external references
        plane_history = {}
        plane_history.update({"event": "departure", "departure_time": plane.departure_time, "origin": plane.origin, "destination": plane.destination})
        plane_history.update({"gate": {"$ref": "gates", "$id": gate_id}})
        plane_history.update({"runway": {"$ref": "runways", "$id": runway_id}})

        self.connector.update_history("planes", plane.airplane_id, plane_history)

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

