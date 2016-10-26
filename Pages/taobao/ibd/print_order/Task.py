from Pages.taobao.ibd.print_order.printorder import PrintOrder
from Pages.taobao.ibd.print_order.print_db_manager import PrintDBManager
from selenium import webdriver


b = PrintDBManager("inventory.csv")
a = PrintOrder(webdriver.Chrome("/Users/jiangjiang/Desktop/Code Projects/Python/chromedriver"), b)
a.start()
