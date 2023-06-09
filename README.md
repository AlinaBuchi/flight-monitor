# Flight Monitor 
Project simulating airport flight monitoring activities:
gate and runway allocation, landing, take-off.

## Table of Contents

- [About](#about)
- [Technologies](#technologies)
- [Installing](#installing)
- [Usage](#usage)
- [API](#api)
- [Tests](#tests)
- [Acknowledgements](#acknowledgements)

## About

Springvale airport needs a monitoring system for landing airplanes.
Being a relatively small airport, it has 4 gates:

* 3 for domestic flights
* 1 for international flights
In case of emergencies, there is also an available hangar for aircraft repairs.

The airport has 2 landing runways.
Domestic flights arrive every hour, while international flights arrive only at 07:00 or 21:00.
Once landed, an airplane is required to stay for 2 hours for checks, refueling, boarding, etc.
Airplanes coming for repairs stay between 2-5 days.

For a proper functioning of the airport and compliance with standards, the following need to be constantly inventoried:

* airplane

-> id   
-> number  
-> airplane model  
-> flight type (DOM/INT)  
-> source  
-> destination (for domestic flights, it's Springvale Airport)

* landing

-> reason (layover, destination, repairs)  
-> landing time  
-> runway used  
-> departure  

* gate

-> departure time  
-> runway used

The project has been created to run both locally connected to the mongo database
while also running on docker. In both cases endpoints related to airplanes 
can be accessed and checked as well on Postman.

Thread example running in terminal:
![thread_example](src/images/thread_example.PNG)

Postman endpoint:
![postman_endpoint](src/images/postman_endpoint.PNG)

Docker container running:
![docker_container](src/images/docker_container.PNG)

## Technologies
python = "^3.10"  
pytest = "^7.2.1"  
flake8 = "^6.0.0"  
pydantic = "^1.10.6"  
pymongo = "^4.3.3"  
fastapi = "^0.95.1"  
uvicorn = "^0.22.0"  
Docker  
MongoDB

## Installing
Docker and Mongo need to be installed separately.
DB needs to have already the gates and runways collections with documents.
For using containers -> 
use <docker-compose build> to build the image and 
<docker-compose up> to run the container.

## Usage
- main.py   

-> to run the app locally in the terminal. For this, uncomment: 
uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")  

-> for local usage: in database.client --> cls._instance.client = MongoClient("mongodb://localhost:27017")  

-> to use for Docker, uncomment: 
uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info") --> access via all IPs

->  for docker make sure the dependency from docker-compose.yaml is properly set with the DB connection in database.client -->
cls._instance.client = MongoClient("mongodb://database:27017")

-> also, it helped mark the src folder as source root.

- main_old.py  

-> to use threads to automatically generate planes, land them and take-off
-> do not forget to make sure the URI in database.client is set to cls._instance.client = MongoClient("mongodb://database:27017")

## API
API available for airplanes. 
The documentation is automatically generated by fastapi and is available at ({localhost:port}/docs).

## Tests
A couple of tests available: both unit and features.
Pytest fixtures - mostly used.
To run tests, make sure in __init__.py in src you have <import sys
sys.path.append('./src')>.
Run testes with command <pytest> --> +options (-vv etc)

## Acknowledgements
Many thanks to Alexandru Niculae from Nenos Academy for his feedback and guidance.