import sqlite3
import os
import sys

def obu_db_create():
    conn = sqlite3.connect('obu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists obu''')
    c.execute('''CREATE TABLE obu
                 (id integer, latitude real, longitude real, ip text primary key, type text, emergency boolean)''')
    
    c.execute('''INSERT INTO obu VALUES (1,"40.63524","-8.65542","192.168.98.30", "AMBULANCE", True)''')
    c.execute('''INSERT INTO obu VALUES (2,"40.6406","-8.64841","192.168.98.40", "FIRE", False)''')
    c.execute('''INSERT INTO obu VALUES (3,"40.6305","-8.65402","192.168.98.50", "POLICE", False)''')
    c.execute('''INSERT INTO obu VALUES (4,"40.64091","-8.659","192.168.98.60", "CAR", False)''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    obu_db_create()