import sqlite3
import os
import sys

def obu_db_create():
    conn = sqlite3.connect('obu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists obu''')
    c.execute('''CREATE TABLE obu
                 (id integer, ilatitude real, ilongitude real, flatitude real, flongitude real, ip text primary key, type text, emergency boolean)''')
    
    c.execute('''INSERT INTO obu VALUES (1,"40.635125", "-8.655874","40.630888", "-8.649292","192.168.98.30", "AMBULANCE", True)''')
    c.execute('''INSERT INTO obu VALUES (2,"40.627138", "-8.661054","40.638840", "-8.657047","192.168.98.40", "CAR", False)''')
    c.execute('''INSERT INTO obu VALUES (3,"40.630633", "-8.653882","40.638940", "-8.650564","192.168.98.50", "POLICE", False)''')
    c.execute('''INSERT INTO obu VALUES (4,"40.631635", "-8.657348","40.638562", "-8.656779","192.168.98.60", "FIRE", False)''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    obu_db_create()
