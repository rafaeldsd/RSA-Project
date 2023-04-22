import sqlite3
import os
import sys

def rsu_db_create():
    conn = sqlite3.connect('rsu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists rsu''')
    c.execute('''CREATE TABLE rsu
                 (id integer, latitude real, longitude real, ip text primary key)''')
    
    c.execute('''INSERT INTO rsu VALUES (1,"40.64154", "-8.65802","192.168.98.15")''')
    c.execute('''INSERT INTO rsu VALUES (2,"40.64074", "-8.65705","192.168.98.16")''')
    c.execute('''INSERT INTO rsu VALUES (3,"40.63476", "-8.66038","192.168.98.17")''')
    c.execute('''INSERT INTO rsu VALUES (4,"40.63544", "-8.65537","192.168.98.18")''')
    c.execute('''INSERT INTO rsu VALUES (5,"40.63319", "-8.65590","192.168.98.19")''')
    
    conn.commit()
    conn.close()