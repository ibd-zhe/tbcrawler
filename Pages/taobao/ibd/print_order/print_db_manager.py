from DataManager.iteminfodb import ibd_dbinfo
import psycopg2
from datetime import datetime
import csv


class PrintDBManager:
    # [[tsc, itemid, color_keyword, inventory, px]]
    def __init__(self, csv_path):
        self.dbinfo = ibd_dbinfo
        with open(csv_path) as file:
            reader = csv.reader(file)
            data = list(reader)
        self.data = self.format(data)
        self.tsc_list = [i[0] for i in self.data]
        self.validate_tsc(self.tsc_list)
        self._con = None
        self.item_px = None
        self.log = []

    def rollback(self, times):
        for i in range(len(self.log) - 1, len(self.log) - 1 - times, -1):
            self.data[self.log[i][0]][3] += self.log[i][1]

    def format(self, data):
        return [[i[0], int(i[1]), i[2], int(i[3]), float(i[4])] for i in data[1:]]

    def validate_tsc(self, tsc_list):
        assert len(tsc_list) == len(set(tsc_list)), "duplicate tsc"

    def check_pq(self, info):
        index = self.find_index(info)
        if index:
            p = self.data[index][4]
            q = self.data[index][3]
            if q > 0:
                if q > info['q']:
                    self.deduct(index, info['q'])
                    return p, info['q']
                else:
                    self.deduct(index, q)
                    return p, q
            else:
                return 0, 0
        else:
            px = self.find_px_in_db(info['itemid'], info['color'])
            return px, 0

    def deduct(self, index, amount):
        self.data[index][3] -= amount
        self.log.append([index, amount])

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

    def find_index(self, info):
        index = self.find_index_by_tsc(info['tsc'])
        if index:
            return index
        else:
            return self.find_index_by_color(info['itemid'], info['color'])

    def find_index_by_color(self, itemid, color):
        try:
            index = [index for index, i in enumerate(self.data) if i[1] == itemid and i[2] in color.upper()]
            if len(index) > 1:
                raise ValueError
            if index:
                return index[0]
            else:
                return None
        except (TypeError, AttributeError):
            return None

    def find_index_by_tsc(self, tsc):
        try:
            tsc_index = [index for index, i in enumerate(self.tsc_list) if i in tsc.upper()]
            if len(tsc_index) > 1:
                raise ValueError
            if tsc_index:
                return tsc_index[0]
            else:
                return None
        except (TypeError, AttributeError):
            return None

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
