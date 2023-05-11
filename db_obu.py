import sqlite3
import os
import sys

def obu_db_create():
    conn = sqlite3.connect('obu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists obu''')
    c.execute('''CREATE TABLE obu
                 (id integer, latitude real, longitude real, ip text primary key, type text, emergency boolean)''')
    
    c.execute('''INSERT INTO obu VALUES (3,null,null,"192.168.98.30", "AMBULANCE", 1)''')
    c.execute('''INSERT INTO obu VALUES (4,null,null,"192.168.98.40", "FIRE", 0)''')
    c.execute('''INSERT INTO obu VALUES (5,null,null,"192.168.98.50", "POLICE", 0)''')
    c.execute('''INSERT INTO obu VALUES (6,null,null,"192.168.98.60", "CAR", 0)''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    obu_db_create()