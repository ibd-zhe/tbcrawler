import psycopg2

ibd_dbinfo = "dbname='ibdtbdata' user='ec2-user' host='54.223.65.44' password='8326022'"


class IbdDB:
    def __init__(self):
        self.dbinfo = ibd_dbinfo
        self.con = psycopg2.connect(self.dbinfo)
        self.cur = self.con.cursor()

    def insert_item(self, item):
        self.cur.execute(
            """INSERT INTO tb_item (itemid, shopid, sku_changed) VALUES (%s, 72076881, TRUE)""", (item['itemid'], ))