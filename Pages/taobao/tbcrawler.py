from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Pages.page import Page
import time

class TBCrawler(Page):
    def __init__(self, driver):
        super().__init__(driver)
        self.home_url = "https://www.taobao.com"
        self.login_url = 'https://login.taobao.com/member/login.jhtml'
        self.login_LJ = {'username': 'leaningho@yahoo.com', 'pwd': '#l#j881023'}

    def goto_home(self):
        self.driver.get(self.home_url)

    def home_search(self, search_field):
        self.goto_home()
        search = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'search-combobox-input')))
        search.send_keys(search_field)
        search_bt = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-search')))
        search_bt.click()

    def goto_login(self):
        self.driver.get(self.login_url)

    def login(self):
        self.goto_login()
        time.sleep(10)
        pwd_login = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='login-links']/a[@class='forget-pwd J_Quick2Static']")))
        ActionChains(self.driver).move_to_element(pwd_login).click(pwd_login).perform()

    def enter_info(self):
        username_tag = 'TPL_username'
        password_tag = 'TPL_password'
        username = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, username_tag)))
        password = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, password_tag)))
        username.send_keys(self.login_LJ['username'])
        password.send_keys(self.login_LJ['pwd'])
        self.driver.find_elements_by_xpath("//button[@class='J_Submit']")[1].send_keys(Keys.RETURN)

    def goto_seller_admin(self):
        self.login()
        seller_admin = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, '卖家中心')))
        seller_admin.click()

    def goto_sellings(self):
        self.goto_seller_admin()
        good_sell = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, '出售中的宝贝')))
        good_sell.click()

    def goto_sold(self):
        self.goto_seller_admin()
        goods_sold = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, '已卖出的宝贝')))
        goods_sold.click()

    def relogin(self):
        tb = TBCrawler(self.driver)
        tb.goto_seller_admin()
        tb.login()
        tb.goto_seller_admin()


class MultiPageTBCrawler(TBCrawler):
    def __init__(self, driver):
        super().__init__(driver)
        self.current_page = 1

    def prepare(self):
        pass

    def done(self):
        pass

    def start(self):
        self.prepare()
        self.check_pagenumber()
        self.crawl_curr_page()
        while self.next_page_element:
            self.goto_next_page()
            self.current_page += 1
            self.check_pagenumber()
            self.crawl_curr_page()
        self.done()
        print("done")

    def check_pagenumber(self):
        pass

    @property
    def next_page_element(self):
        return 1

    def goto_next_page(self):
        pass

    def crawl_curr_page(self):
        pass