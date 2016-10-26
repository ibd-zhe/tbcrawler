import unittest
from Pages.taobao.ibd.print_order.print_db_manager import PrintDBManager
from datetime import datetime


class PrintDBTest(unittest.TestCase):
    def setUp(self):
        self.pdb = PrintDBManager("inventory.csv")
        self.info1 = [
            {'eg': {'tsc': 'WNW909D', 'color': '909', 'itemid': 44572730041, 'q': 4}, 'an': (18, 4)},
            {'eg': {'tsc': 'WNW90', 'color': '909', 'itemid': 44572730041, 'q': 4}, 'an': (18, 4)},
            {'eg': {'tsc': None, 'color': '909', 'itemid': 44572730041, 'q': 4}, 'an': (18, 4)},
            {'eg': {'tsc': 'WNW9', 'color': '99', 'itemid': 44572730041, 'q': 4}, 'an': (0, 0)},
            {'eg': {'tsc': 'WNW90D', 'color': '909', 'itemid': 6457230041, 'q': 4}, 'an': (0, 0)},
            {'eg': {'tsc': None, 'color': '909', 'itemid': 44572730041, 'q': 150}, 'an': (18, 111)},
            {'eg': {'tsc': None, 'color': '', 'itemid': 44572730041, 'q': 4}, 'an': (0, 0)},
            {'eg': {'tsc': 'WNW909D', 'color': '', 'itemid': 44572730041, 'q': 123}, 'an': (0, 0)},
        ]

    def testFormat(self):
        assert len(self.pdb.data) == 26
        assert isinstance(self.pdb.data[0][0], str)
        assert isinstance(self.pdb.data[0][1], int)
        assert isinstance(self.pdb.data[0][2], str)
        assert isinstance(self.pdb.data[0][3], int)
        assert isinstance(self.pdb.data[0][4], float)

    def testFindOrder(self):
        assert self.pdb.date_of_order(1) == datetime(2016, 10, 19)
        assert self.pdb.date_of_order(2571595868349039) == datetime(2016, 10, 19, 2, 48, 16)

    def testPQColor(self):
        assert self.pdb.find_index_by_color(1, 's') is None
        assert self.pdb.find_index_by_color(44572730041, '900') == 0
        assert self.pdb.find_index_by_color(44572730042, '900') is None
        assert self.pdb.find_index_by_color(44572730041, '800') is None

    def testTscColor(self):
        assert self.pdb.find_index_by_tsc('WNW909D') == 9
        assert self.pdb.find_index_by_tsc('WNW909') == 9
        assert self.pdb.find_index_by_tsc('WNW90') is None

    def testCheckPQ(self):
        for i in self.info1:
            assert self.pdb.check_pq(i['eg']) == i['an']

if __name__ == '__main__':
    unittest.main()

