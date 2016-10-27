from Pages.taobao.ibd.print_order.printorder import PrintOrder
from Pages.taobao.ibd.print_order.print_db_manager import PrintDBManager
from selenium import webdriver
import sys
sys.path.append('D:\\Code\\tbcrawler')

b = PrintDBManager("inventory.csv")
a = PrintOrder(webdriver.Ie('IEDriverServer.exe'), b)

