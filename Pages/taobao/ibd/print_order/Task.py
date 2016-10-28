from Pages.taobao.ibd.print_order.printorder import PrintOrder
from Pages.taobao.ibd.print_order.print_db_manager import PrintDBManager
from selenium import webdriver
import sys


def ss(time=None):
    b = PrintDBManager('inventory.csv')
    a = PrintOrder(webdriver.Chrome(
        "/Users/jiangjiang/Desktop/Code Projects/Python/chromedriver"), b, time)
    a.start()


if __name__ == '__main__':
    try:
        ss(sys.argv[1].split('#'))
    except IndexError:
        ss()