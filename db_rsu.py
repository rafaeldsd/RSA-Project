import sqlite3
import os
import sys

def rsu_db_create():
    conn = sqlite3.connect('rsu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists rsu''')
    c.execute('''CREATE TABLE rsu
                 (id integer, latitude real, longitude real, ip text primary key)''')
    
    c.execute('''INSERT INTO rsu VALUES (10,"40.63476", "-8.66038","192.168.98.70")''')
    c.execute('''INSERT INTO rsu VALUES (11,"40.63544", "-8.65537","192.168.98.80")''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    rsu_db_create()