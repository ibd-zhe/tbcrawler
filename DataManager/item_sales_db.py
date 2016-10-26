from DataManager.psycopg_err_handle import find_key_name
from DataManager.iteminfodb import ibd_dbinfo
import psycopg2
from psycopg2 import IntegrityError
from datetime import datetime


class ItemSalesDB:
    def __init__(self):
        self.data = None
        self.dbinfo = ibd_dbinfo
        self.con = psycopg2.connect(self.dbinfo)
        self.cur = self.con.cursor()

    # data format: {'number': int, 'items': {}, 'ordertime':datetime, 'user_id': str, 'state': str, 'total': float}
    def start(self, data):
        self.data = data['data']
        self.update_order_state()

        if data['mission'] == 'insert':
            self.insert_ibd_item_sales()
        else:
            self.update_states()

    def update_states(self):
        self.update_order_state()
        self.update_items_states()

    def update_items_states(self):
        for index, i in enumerate(self.data['items']):
            print(" ")
            print("update state for " + str(index) + " item")
            i['ordernumber'] = self.data['number']
            self.update_item_state(i)

    def update_item_state(self, item):
        self.cur.execute(
            """UPDATE ibd_item_sales SET state=%(state)s WHERE ordernumber=%(ordernumber)s AND
        item_color_id=(SELECT id FROM item_real_map_tb WHERE tb_item=%(itemid)s AND tb_color=%(color)s)""", item)

    def insert_ibd_item_sales(self):
        for index, i in enumerate(self.data['items']):
            print(" ")
            print("write db for " + str(index) + " item")
            i['ordernumber'] = self.data['number']
            self.insert_itemsales(i)

    def update_order_state(self):
        try:
            self.cur.execute(
                """UPDATE orderhist SET state=%s WHERE number=%s""", (self.data['state'], self.data['number']))
        except IntegrityError:
            self.con.rollback()
            self.insert_order()
        finally:
            self.con.commit()

    def filter(self):
        if self.data['order_time'] > datetime(2016, 9, 28, 0, 0, 0):
            self.insert_order()

    # item format {'tsc': str, 'itemid': int, 'color': str, 'price': float, 'quantity': int, 'state': str}
    def insert_itemsales(self, item):
        if item['color'] is None:
            item['color'] = 'OnlyOneSku'
        self.insert_by_itemcolor(item)

    def insert_by_itemcolor(self, item):
        try:
            self.cur.execute(
                """INSERT INTO ibd_item_sales VALUES (%(ordernumber)s, %(price)s, %(quantity)s, %(state)s, (SELECT id FROM
item_real_map_tb WHERE tb_item=%(itemid)s AND tb_color=%(color)s))""", item)
        except IntegrityError as e:
            self.con.rollback()
            key = find_key_name(str(e))
            if key[0] == 'null':
                self.insert_itemtsc(item)
                self.insert_by_itemcolor(item)
            elif key[1] == 'ordernumber':
                self.insert_order()
                self.insert_by_itemcolor(item)
            else:
                print("has itemsales for order " + str(self.data['number']) + "   " + str(item['itemid']))
        else:
            self.con.commit()
            print("insert ibd_item_sales")

    def insert_itemtsc(self, item):
        try:
            self.insert_itemtsccolor(item)
        except IntegrityError as e:
            self.con.rollback()
            key = find_key_name(str(e))[1]
            if key == 'tb_item':
                self.insert_item(item['itemid'], item['title'])
            elif key == 'tb_item, tb_color':
                raise ValueError
        else:
            self.con.commit()
            print("insert item_real_map_tb, item: " + str(item['itemid']))

    def update_item_skuchange(self, itemid):
        self.cur.execute("""UPDATE tb_item SET sku_changed = TRUE WHERE itemid=%s""", (itemid, ))

    def insert_item(self, itemid, title=None):
        self.cur.execute(
            """INSERT INTO tb_item (itemid, shopid, sku_changed) VALUES (%s, 72076881, TRUE)""",
            (itemid, ))
        if title is not None:
            self.insert_title_for_item(itemid, title)
        print("insert item  " + str(itemid))
        self.con.commit()

    def insert_order(self):
        try:
            self.cur.execute(
                """INSERT INTO orderhist (number, state, price, time, userid, only_minimum)
            VALUES (%(number)s, %(state)s, %(total)s, %(order_time)s, %(user_id)s, TRUE)""", self.data)
        except IntegrityError:
            self.con.rollback()
            pass
        else:
            self.con.commit()
            print("insert order " + str(self.data['number']))

    def insert_itemtsccolor(self, item):
        self.cur.execute(
            """INSERT INTO item_real_map_tb (id, tb_item, tb_tsc, tb_color)
                VALUES (DEFAULT, %(itemid)s, %(tsc)s, %(color)s)""", item)
        print("insert new itemcolortsc, item: " + str(item['itemid']))

    def itemid_of_title(self, title):
        self.cur.execute("""SELECT itemid FROM tb_item_title WHERE title=%s""", (title, ))
        a = self.cur.fetchall()
        if len(a) == 1:
            return a[0][0]
        elif len(a) > 1:
            return "NOT_ONLY"

    def insert_title_for_item(self, itemid, title):
        try:
            self.cur.execute("""INSERT INTO tb_item_title (itemid, title) VALUES (%s, %s)""", (itemid, title))
            print("insert new title")
        except IntegrityError:
            self.con.rollback()
            self.insert_item(itemid, title)
        else:
            self.con.commit()

    def check_ordernumber(self, ordernumber):
        self.cur.execute("""SELECT COUNT(*) FROM ibd_item_sales WHERE ordernumber=%s""", (ordernumber, ))
        return self.cur.fetchone()[0]
