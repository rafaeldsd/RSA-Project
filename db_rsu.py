import sqlite3
import os
import sys

def rsu_db_create():
    conn = sqlite3.connect('rsu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists rsu''')
    c.execute('''CREATE TABLE rsu
                 (id integer, latitude real, longitude real, ip text primary key)''')
    
    c.execute('''INSERT INTO rsu VALUES (1,"40.64154", "-8.65802","192.168.98.70")''')
    c.execute('''INSERT INTO rsu VALUES (2,"40.64074", "-8.65705","192.168.98.80")''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    rsu_db_create()