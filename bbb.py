from selenium import webdriver
from Pages.taobao.tbcrawler import TBCrawler
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import csv
from Pages.taobao.ibd.print_order.print_db_manager import PrintDBManager
from Pages.taobao.ibd.print_order.printorder import PrintOrder

a = webdriver.Ie('IEDriverServer.exe')
bbb = PrintDBManager("inventory.csv")
b = PrintOrder(a, bbb)
b.goto_login()

