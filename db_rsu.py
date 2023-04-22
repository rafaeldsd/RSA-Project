import sqlite3
import os
import sys

def rsu_db_create():
    conn = sqlite3.connect('rsu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists rsu''')
    c.execute('''CREATE TABLE rsu
                 (latitude real, longitude real, ip text primary key)''')
    
    # c.execute('''INSERT INTO rsu VALUES (null,null,"192.168.98.15")''')

    conn.commit()
    conn.close()