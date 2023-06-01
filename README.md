# Emergency Vehicle Notification System (RSA)

## Introduction

We are proposing a solution to address the significant risks faced by emergency services while responding to emergencies, especially in highly congested urban areas. The project aims to provide real-time notifications about the location and status of emergency vehicles to nearby vehicles, helping drivers quickly and safely clear the path of the emergency vehicle. This, in turn, reduces the risk of accidents and improves response times.

## Project Overview

The project utilizes VANETZA to equip emergency vehicles with the ability to send DENM messages to nearby vehicles, containing information about their location, speed, and direction of travel. The DENM message may also include details about the type of emergency. Within a specified range, vehicles receive the DENM message and inform the driver through a message displayed on the dashboard or an audible warning. The notification can also indicate the current location and the direction in which the emergency vehicle is heading. Additionally, a central server receives the DENM message, which is then utilized to monitor the real-time location and status of emergency vehicles.

## Installation
To run the project locally, follow these basic instructions:

1. Create a virtual environment (venv)
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install the game requirements:
```bash
pip install -r requirements.txt
```
## Usage

To run the project, follow these steps:

1. Open four terminals
2. Run the docker compose (1st terminal)
```bash
docker-compose up
``` 
3. Run the webapp (2nd terminal)
```bash
python3 app.py
``` 
4. Run the simulation for the RSU's (3rd terminal)
 ```bash
python3 simulation_rsu.py
```
5. Run the simulation for the OBU's (4th terminal)
```bash
python3 simulation_obu.py
```

## Modifying Routes in the Database

To modify the routes in the database, follow these steps:

1. Open the `db_rsu.py` and `db_obu.py` files in your preferred text editor.

2. Locate the section where the latitude and longitude values for the routes are defined.

3. Update the latitude and longitude values according to the desired modifications. 

4. Save the changes made to the `db_rsu.py` and `db_obu.py` files.

5. Run the `coordinates.py` script to update the database with the modified routes. Use the following command:
```bash
python coordinates.py
```

## References

Here are some useful references that can be consulted for more information:

- [VANETZA Documentation](https://code.nap.av.it.pt/mobility-networks/vanetza)
- [ETSI C-ITS Standards for CAMS](https://www.etsi.org/deliver/etsi_EN/302600_302699/30263702/01.04.01_30/en_30263702v010401v.pdf)
- [ETSI C-ITS Standards for DENMS](https://www.etsi.org/deliver/etsi_en/302600_302699/30263703/01.02.01_30/en_30263703v010201v.pdf)
- [Intelligent Transportation Systems](https://en.wikipedia.org/wiki/Intelligent_transportation_system)
