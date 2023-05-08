# built-in imports
import random as rnd
import time
import threading as th
from typing import Callable, Union
from datetime import datetime, timedelta

# local app imports
from models import (
    AirplaneDomesticFlight,
    AirplaneInternationalFlight,
    Airplane
)
from airport import Airport


airport = Airport('Springvale')


def validate_airplane_attributes(reason: str, origin: str, destination: str, flight_type: str) -> bool:
    if flight_type == 'International' and origin not in ['Autumnvale', 'Wintervale', 'Summervale']:
        if (destination != 'Springvale' and reason == 'connection') or (
                destination == 'Springvale' and reason == 'destination'):
            return True
    elif flight_type == 'Domestic' and reason in ['destination',
                                                  'repair'] and destination == 'Springvale' and origin in ['Autumnvale',
                                                                                                           'Wintervale',
                                                                                                           'Summervale']:
        return True
    return False


def get_random_airplane_attributes() -> dict[str, Union[int, str, str, datetime, str, str, str]]:
    """
    get random K: V to use as arguments in creating a plane object(pydantic)
    """
    random_attr_dict = dict(
        airplane_id=rnd.randrange(111111, 999999, 6),
        model=rnd.choice(['Boeing 737', 'Boeing 787', 'Airbus A330', 'Boeing 777', 'Airbus A320']),
        reason=rnd.choices(['destination', 'connection', 'repair'], weights=(45, 15, 40), k=1)[0],
        flight_time=datetime(2023, 3, 7, 13, 00) + timedelta(minutes=rnd.randrange(60)),
        origin=rnd.choice(
            ['Paris', 'Singapore', 'Dubai', 'Rome', 'Prague', 'Autumnvale', 'Wintervale', 'Summervale', 'New York']),
        destination=rnd.choices(
            ['Istanbul', 'Bali', 'Lisbon', 'Bucharest', 'Nice', 'Autumnvale', 'Wintervale', 'Summervale', 'New York',
             'Springvale'], weights=(5, 5, 5, 5, 5, 5, 5, 5, 5, 60), k=1)[0],
        flight_type=rnd.choices(['Domestic', 'International'], weights=(30, 70), k=1)[0])
    if random_attr_dict['flight_type'] == 'Domestic':
        random_attr_dict['flight_time'] = datetime(2023, 3, 7, 13, 00) + timedelta(minutes=rnd.randrange(60))
    elif random_attr_dict['flight_type'] == 'International':
        random_attr_dict['flight_time'] = rnd.choice([datetime(2023, 3, 7, 7, 00), datetime(2023, 3, 7, 21, 00)])

    return random_attr_dict


def generate_random_airplane() -> Airplane:
    """
    Generate random attributes, validate them and create an object.
    """
    while True:
        data = get_random_airplane_attributes()
        if validate_airplane_attributes(data['reason'], data['origin'],
                                        data['destination'], data['flight_type']):

            if data['flight_type'] == 'Domestic':
                return AirplaneDomesticFlight(**data)
            else:
                return AirplaneInternationalFlight(**data)


def do_backup_json() -> None:
    airport.export_arrivals()
    airport.export_departures()


def execution_duration(func: Callable[[...], None]) -> Callable:
    """
    Decorator: Shows the execution duration of the function object passed
    """
    def wrap_func(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        print(f'Function {func.__name__!r} executed in {(t2 - t1):.4f}s \n')
        return result

    return wrap_func


@execution_duration
def thread_consume_arrival_queue() -> None:
    """
    Queue to consume arrival queue if we have items.
    if plane can't arrive after being taken from the queue, we put it back in again.
    """
    while True:
        time.sleep(5)
        if airport.arrivals_queue.qsize() > 0:
            plane = airport.arrivals_queue.get()
            print(f'THREAD CONSUME ARRIVAL START - {plane.airplane_id} - {plane.flight_type} \n')
            airport.arrive_plane(plane)
            print('Airplane has arrived from another try')
        else:
            print('Arrival queue break')
            break


@execution_duration
def thread_consume_depart_queue() -> None:
    """
        Queue to consume departure queue if we have items.
        if plane can't depart after being taken from the queue, we put it back in again.
        Count to break the loop - in place.
        """
    count = 0
    time.sleep(10)
    while True:
        time.sleep(5)
        if airport.departures_queue.qsize() > 0:
            plane = airport.departures_queue.get()
            print(f'THREAD CONSUME DEPARTURE START - {plane.airplane_id} - {plane.flight_type} \n')
            airport.depart_plane(plane, 3)

            print('Airplane has departed from consumer queue')
        elif airport.departures_queue.qsize() == 0:
            count += 1
            if count == 15:
                print('Departure queue break')
                break


@execution_duration
def thread_produce_queue_arrive():
    """
        Queue to produce planes.
        if plane can't arrive, we put it in the arrival queue.
        """
    print('Producer: Running')
    # generate work - 5 planes
    for i in range(5):
        # generate a value
        print()
        plane = generate_random_airplane()
        result = plane.dict()
        result.update({'history': []})

        airport.connector.insert_one("planes", result)
        print('-----RANDOM PLANE -> GENERATED-----')
        print()
        print(plane)

        airport.arrivals_queue.put(plane)

    print('Producer: Done')


threads: list[th.Thread] = []

if __name__ == "__main__":

    # queue producer
    thread_produce_queue_arrive = th.Thread(target=thread_produce_queue_arrive)
    threads.append(thread_produce_queue_arrive)

    # queue consume arrival
    thread_consume_queue = th.Thread(target=thread_consume_arrival_queue)
    threads.append(thread_consume_queue)

    # depart thread
    thread_consume_depart_queue = th.Thread(target=thread_consume_depart_queue)
    threads.append(thread_consume_depart_queue)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    do_backup_json()
