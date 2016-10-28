import sqlite3
import csv
from random import randint

con = sqlite3.connect('ibd-print.db')
cur = con.cursor()
cur.execute("SELECT * FROM inventory")


def writeinv():
    with open('inventory' + str(randint(0, 9)) + '.csv', 'w') as f:
        aa = csv.writer(f)
        aa.writerows(cur.fetchall())
