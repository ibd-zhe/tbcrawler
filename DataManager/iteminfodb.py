import psycopg2
from psycopg2 import IntegrityError
import uuid
from DataManager.psycopg_err_handle import find_key_name

ibd_dbinfo = "dbname='ibdtbdata' user='ec2-user' host='54.223.65.44' password='8326022'"


class ItemDB:
    def __init__(self, data=None):
        self.dbinfo = ibd_dbinfo
        if data is not None:
            self.item = data['item']
            self.skus = data['skus']
        self.con = psycopg2.connect(self.dbinfo)
        self.cur = self.con.cursor()

    @property
    def if_has_tsc(self):
        self.cur.execute("""SELECT * FROM item_real_map_tb WHERE tb_item=%s""", (self.item['itemid'], ))
        if self.cur.fetchone():
            print("already has tsc")
            return True
        else:
            return False

    def write_tbitem(self):
        try:
            self.cur.execute(
                """INSERT INTO taobao.tb_item VALUES(%(itemid)s, %(cid)s, %(brand)s, %(title)s, %(shopid)s)""",
                self.item)
        except IntegrityError as e:
            key = find_key_name(str(e))[1]
            if key == 'itemid':
                print("old item: " + str(self.item['itemid']))
                self.con.rollback()
            elif key == 'tb_cid':
                self.con.rollback()
                self.cur.execute("""INSERT INTO taobao.tb_cat (categoryid) VALUES (%s)""", (self.item['cid'],))
                self.con.commit()
                print('insert new cid: ' + str(self.item['cid']))
                self.write_tbitem()
            else:
                print("New Unseen Key!!  " + str(self.item['itemid']))
        else:
            self.con.commit()
            print("new item " + str(self.item['itemid']))

    def write_detail(self):
        if self.item['brand'] is not None:
            self.update_brand()
        self.write_skus()

    def update_brand(self):
        try:
            self.cur.execute("""UPDATE taobao.tb_item SET tb_brand=(%s) WHERE itemid=(%s)""",
                             (self.item['brand'], self.item['itemid']))
        except IntegrityError as e:
            key = find_key_name(str(e))[1]
            if key == 'tb_brand':
                self.con.rollback()
                self.cur.execute("""INSERT INTO taobao.tb_brand (name) VALUES (%s)""", (self.item['brand'],))
                print("insert new brand: " + self.item['brand'])
                self.update_brand()
            else:
                print("update brand wrong for item: " + str(self.item['itemid']))

    def write_skus(self):
        if self.skus is not None:
            for i in self.skus:
                self.write_sku(i)
            print("add new tsc")

    def write_sku(self, sku):
        sku["itemid"] = self.item["itemid"]
        if sku['upc'] == '':
            sku['upc'] = None
        if sku['tsc'] == '':
            print("impossible")
            sku['tsc'] = None
        else:
            self.write_tsc(sku['tsc'])
        self.cur.execute(
            """INSERT INTO item_real_map_tb VALUES(DEFAULT, %(itemid)s, %(tsc)s, %(color)s, %(px)s, %(quantity)s, %(upc)s)""",
            sku)

    def write_tsc(self, tsc):
        self.cur.execute("""INSERT INTO real_item (tsc) VALUES(%s)""", (tsc,))

    def commit_db(self):
        self.con.commit()
        self.con.close()

    def validate_tsc(self, tsc):

        if tsc == '':
            print("empty tsc, generate new one")
            return self.generate_tsc()
        else:
            con1 = psycopg2.connect(self.dbinfo)
            cur1 = con1.cursor()
            cur1.execute("""SELECT * FROM real_item WHERE tsc=%s""", (tsc, ))
            if cur1.fetchone():
                con1.close()
                print("repititive tsc, modified")
                return self.add_tsc(tsc)
            else:
                con1.close()
                return tsc

    def add_tsc(self, tsc):
        random = self.generate_tsc()
        return tsc + random

    def generate_tsc(self):
        random6 = uuid.uuid4().hex[:6]
        return random6
