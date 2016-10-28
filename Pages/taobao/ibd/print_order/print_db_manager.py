from DataManager.iteminfodb import ibd_dbinfo
import psycopg2
from datetime import datetime
import csv
import sqlite3
from Pages.taobao.ibd.print_order.orderitem import itemidlist


class PrintDBManager:
    # [[tsc, itemid, color_keyword, inventory, px]]
    def __init__(self, csvf=None):
        self.dbinfo = ibd_dbinfo
        self._con = None
        self.log = []
        self.pycon = sqlite3.connect('ibd-print.db')
        self.pycur = self.pycon.cursor()
        if csvf:
            self.read_from_csv(csvf)

    def read_from_csv(self, csvf):
        with open(csvf) as file:
            reader = csv.reader(file)
            data = list(reader)
        data1 = self.format(data)
        tsc_list = [i[0] for i in data1]
        self.validate_tsc(tsc_list)
        self.write_to_sqlite(data1)

    def write_to_sqlite(self, data):
        print('read csv')
        self.pycur.execute("""DELETE FROM inventory""")
        self.pycur.executemany("INSERT INTO inventory VALUES (?,?,?,?,?)", data)
        self.pycon.commit()

    def printout(self):
        printed_color = set([i[0] for i in self.log])
        printed_number = [[i, sum([j[1] for j in self.log if j[0] == i])] for i in printed_color]
        left = self.get_colnum(list(printed_color))
        for i in printed_number:
            print(i[0] + "已发" + str(i[1]) + '个. ' + '还剩' + str(left[[j[0] for j in left].index(i[0])][1]) +
                  '个')

    def get_colnum(self, color_list):
        query = '(' + ','.join('?' for i in color_list) + ')'
        self.pycur.execute("SELECT color,inventory FROM inventory WHERE color IN" + query, color_list)
        return self.pycur.fetchall()

    def rollback(self, times):
        for i in range(len(self.log) - 1, len(self.log) - 1 - times, -1):
            self.pycur.execute("UPDATE inventory SET inventory=inventory+? WHERE color=?", (self.log[i][1],
                               self.log[i][0]))
            self.pycon.commit()

    def format(self, data):
        return [[i[0].upper(), int(i[1]), i[2].upper(), int(i[3]), float(i[4])] for i in data[1:]]

    def validate_tsc(self, tsc_list):
        assert len(tsc_list) == len(set(tsc_list)), "duplicate tsc"

    def check_pq(self, info):
        color = self.find_color(info)
        if color:
            p, q = self.pq_by_color(color)
            if q > 0:
                if q > info['q']:
                    self.deduct_by_color(color, info['q'])
                    return p, info['q']
                else:
                    self.deduct_by_color(color, q)
                    return p, q
            else:
                return 0, 0
        else:
            px = self.find_px_in_db(info['itemid'], info['color'])
            return px, 0

    def find_color(self, info):
        if info['itemid'] in itemidlist:
            color = self.color_by_tsc(info['tsc'])
            if color:
                return color
            else:
                return self.color_by_color(info['itemid'], info['color'])

    def deduct_by_color(self, color, q):
        self.pycur.execute("UPDATE inventory SET inventory=inventory-? WHERE color=?", (q, color))
        self.log.append([color, q])
        self.pycon.commit()

    def pq_by_color(self, color):
        self.pycur.execute("SELECT px,inventory FROM inventory WHERE color=?", (color, ))
        return self.pycur.fetchone()

    def color_by_tsc(self, tsc):
        if tsc:
            self.pycur.execute("SELECT color FROM inventory WHERE ? Like '%'||tsc||'%'", (tsc.upper(), ))
            color = self.pycur.fetchone()
            if color:
                return color[0]

    def color_by_color(self, itemid, color):
        try:
            self.pycur.execute("SELECT color FROM inventory WHERE itemid=? AND ? Like '%'||color||'%'", (itemid, color.upper()))
            color = self.pycur.fetchone()
        except (TypeError, AttributeError):
            return None
        else:
            if color:
                return color[0]

    def find_px_in_db(self, itemid, color):
        cur = self.con.cursor()
        cur.execute(
            """SELECT price FROM ibd_item_sales WHERE item_color_id=(SELECT id FROM item_real_map_tb WHERE
            tb_item=%s AND tb_color=%s)""", (itemid, color))
        p = cur.fetchone()
        if p:
            print("found px in db" + str(p[0]))
            return p[0]
        else:
            return 0

    def date_of_order(self, ordernumber):
        cur = self.con.cursor()
        cur.execute("""SELECT time FROM orderhist WHERE number=%s""", (ordernumber, ))
        try:
            return cur.fetchone()[0]
        except TypeError:
            return datetime(2016, 10, 19)

    @property
    def con(self):
        if self._con is None:
            self._con = psycopg2.connect(self.dbinfo)
        return self._con
