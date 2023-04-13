# built-in imports
import random as rnd
import time
import threading as th
from typing import Callable, Union
from datetime import datetime, timedelta

# local app imports
from models.airplane import (
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
        flight_type=rnd.choices(['Domestic', 'International'], weights=(70, 30), k=1)[0])
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
    count = 0
    done = False
    while True:
        time.sleep(1)
        if airport.plane_queue.qsize() > 0:
            plane = airport.plane_queue.get()
            print(f'THREAD CONSUME ARRIVAL START - {plane.airplane_id} - {plane.flight_type} \n')
            is_arrived = airport.arrive_plane(plane)
            if not is_arrived:
                # add to the queue
                airport.plane_queue.put(plane)
            else:
                print('Airplane has arrived from the another try')
        elif done:
            break
        else:
            count += 1
            print(f'Empty arrival plane_queue ...{count=}')
            time.sleep(1)
            if count == 10:
                done = True


@execution_duration
def thread_consume_depart_queue() -> None:
    """
        Queue to consume departure queue if we have items.
        if plane can't depart after being taken from the queue, we put it back in again.
        Count to break the loop - in place.
        """
    count = 0
    done = False
    time.sleep(10)
    while True:
        if airport.awaiting_departure.qsize() > 0:
            plane = airport.awaiting_departure.get()
            print(f'THREAD CONSUME DEPARTURE START - {plane.airplane_id} - {plane.flight_type} \n')
            is_departed = airport.depart_plane(plane, 3)
            if not is_departed:
                # add to the queue
                airport.awaiting_departure.put(plane)
            else:
                print('Airplane has departed from consumer queue')
        elif done:
            break
        else:
            count += 1
            print(f'Empty awaiting_departure ...{count=}')
            time.sleep(2)
            if count == 10:
                done = True


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
        print('-----RANDOM PLANE -> GENERATED-----')
        print()
        print(plane)
        is_arrived = airport.arrive_plane(plane)
        if not is_arrived:
            time.sleep(2)
            # add to the queue
            airport.plane_queue.put(plane)
        else:
            print('Airplane has arrived from the first try')
    # all done
    print('Producer: Done')


running = True


@execution_duration
def do_backup():
    """
    save data
    """
    while running:
        time.sleep(3)
        airport.export_arrivals()
        time.sleep(3)
        airport.export_departures()


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

    # backup started separately to join it with the main thread at the end to get all the data
    thread_backup = th.Thread(target=do_backup)
    thread_backup.start()

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # break the while loop
    running = False
    thread_backup.join()
