import sys

from Pages.taobao.ibd.ibd_data_crawl.SellerItem import SellingItem
from selenium import webdriver
from Pages.taobao.ibd.print_order.printorder import PrintOrder
from DataManager.item_sales_db import ItemSalesDB
from DataManager.iteminfodb import ItemDB
from Pages.taobao.ibd.ibd_data_crawl.SoldItem import SoldItem


def crawl_selling_item():
    driver = webdriver.Chrome("/Users/jiangjiang/Desktop/Code Projects/Python/tbcrawler/chromedriver")
    a = SellingItem(driver, ItemDB)
    a.start()


def add_item_sales(start=None, end=None):
    driver = webdriver.Chrome("/Users/jiangjiang/Desktop/Code Projects/Python/tbcrawler/chromedriver")
    b = ItemSalesDB()
    a = SoldItem(driver, b, begin_time=start, end_time=end)
    a.start()


def print_order():
    a = webdriver.Chrome("/Users/jiangjiang/Desktop/Code Projects/Python/tbcrawler/chromedriver")
    b = PrintOrder(a)
    b.start()

# command line time input 'begin//end', if no begin, '//end'
if __name__ == '__main__':
    if sys.argv[1] == "insert selling item":
        crawl_selling_item()
    elif sys.argv[1] == "itemsales":
        try:
            a = sys.argv[2].split('//')
        except IndexError:
            add_item_sales()
        else:
            add_item_sales(a[0], a[1])
    elif sys.argv[1] == 'printorder':
        print_order()


