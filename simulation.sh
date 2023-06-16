#!/bin/bash

gnome-terminal -e 'python3 simulation_rsu.py' &
gnome-terminal -e 'python3 simulation_obu.py' &
# gnome-terminal -e 'python3 app.py' &