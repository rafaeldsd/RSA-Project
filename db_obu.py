import sqlite3
import os
import sys

def obu_db_create():
    conn = sqlite3.connect('obu.db')
    c = conn.cursor()
    c.execute('''DROP TABLE if exists obu''')
    c.execute('''CREATE TABLE obu
                 (type text, latitude real, longitude real, ip text primary key)''')
    
    # c.execute('''INSERT INTO obu VALUES (0,null,null,"192.168.98.30")''')
    # c.execute('''INSERT INTO obu VALUES (1,null,null,"192.168.98.31")''')
    # c.execute('''INSERT INTO obu VALUES (2,null,null,"192.168.98.32")''')

    conn.commit()
    conn.close()