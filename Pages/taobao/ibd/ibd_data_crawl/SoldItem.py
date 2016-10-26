from datetime import datetime
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from Pages.page import MultiPage
from Pages.taobao.ibd.ibd_data_crawl.OrderCrawler import OrderCrawler
from Pages.taobao.tbcrawler import TBCrawler


# time format '2015-08-08 13:40:50'
class SoldItem(MultiPage):
    def __init__(self, driver, data_manager, begin_time=None, end_time=None):
        super().__init__(driver)
        self.data_manager = data_manager
        self.end_time = end_time
        self.begin_time = begin_time

    def prepare(self):
        tb = TBCrawler(self.driver)
        tb.goto_sold()
        self.check_pagenumber()
        self.filter_time()
        self.display_more_pages()

    def display_more_pages(self):
        bt = WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(), '显示更多页码')]"))
        )
        self.click_link(bt)

        WebDriverWait(
            self.driver, self.page_refresh_time).until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), '跳至')]"))
        )
        self.goto_first_page()
        self.check_pagenumber()

    def goto_first_page(self):
        bt = WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "pagination-item-1"))
        )
        self.click_link(bt)

    def filter_time(self):
        date_changed = False
        if self.end_time:
            self.end_time = datetime.strptime(self.end_time, '%Y-%m-%d %H:%M:%S')
            self.input_datetime(self.end_time, 'end')
            date_changed = True
        if self.begin_time:
            self.begin_time = datetime.strptime(self.begin_time, '%Y-%m-%d %H:%M:%S')
            self.input_datetime(self.begin_time, 'begin')
            date_changed = True
        if date_changed:
            self.search_order()

    def input_datetime(self, time, time_type):
        self.click_time(time_type)
        self.input_date(time)
        self.input_time(time)
        self.sumbit_time()

    def search_order(self):
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(), '搜索订单')]"))
        ).click()
        self.check_search_result()

    def check_search_result(self):
        WebDriverWait(
            self.driver, self.page_refresh_time).until(
            self.if_date_smaller()
        )

    def if_date_smaller(self):
        def predicate(driver):
            try:
                first_time = OrderCrawler(self.driver, 0).order_time
            except StaleElementReferenceException:
                return True
            else:
                print("first" + str(first_time))
                print("end" + str(self.end_time))
                if first_time > self.end_time:
                    return False
                else:
                    return True
        return predicate

    def click_time(self, time_type):
        xpath = None
        if time_type == 'end':
            xpath = "//input[@placeholder='请选择时间范围结束']"
        elif time_type == 'begin':
            xpath = "//input[@placeholder='请选择时间范围起始']"

        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable((By.XPATH, xpath))).click()

    # for fast development, do not change year 2016
    def input_date(self, time):
        self.input_month(time.month)
        self.input_day(time.strftime('%Y-%-m-%-d'))

    def input_year(self, year):
        year_element = WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='rc-calendar-year-select']"))
        )
        if year_element[:4] != year:
            diff = int(year) - int(year_element[:4])

    def input_month(self, month):
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@class='rc-calendar-month-select']"))
        ).click()
        month_dict = {1: '一月', 2: '二月', 3: '三月', 4: '四月', 5: '五月', 6: '六月', 7: '七月', 8: '八月',
                      9: '九月', 10: '十月', 11: '十一月', 12: '十二月'}
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//td[@role='gridcell'][@title='{0}']".format(month_dict[month])))
        ).click()

    def input_day(self, day):
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable((By.XPATH, "//td[@title='{0}']".format(day)))
        ).click()

    def input_time(self, time):
        self.input_hour(time.hour)
        self.input_minute(time.minute)
        self.input_second(time.second)

    def input_hour(self, hour):
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@class='rc-calendar-time-input']"))
        ).click()

        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//td[@class='rc-calendar-time-panel-cell']//*[contains(text(), '{0}')]".format(
                    str(hour))))
        ).click()

    def input_minute(self, minute):
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@class='rc-calendar-time-minute']/input"))
        ).click()

        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//td[@class='rc-calendar-time-panel-cell']//*[contains(text(), '{0}')]".format(
                    str(minute))))
        ).click()

    def input_second(self, second):
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@class='rc-calendar-time-second']/input"))
        ).click()

        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//td[@class='rc-calendar-time-panel-cell']//*[contains(text(), '{0}')]".format(
                    str(second))))
        ).click()

    def sumbit_time(self):
        WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@class='rc-calendar-ok-btn']"))
        ).click()

    def check_pagenumber(self):
        WebDriverWait(self.driver, 5).until(self.page_equal_to(self.current_page))

    def page_equal_to(self, page):
        def predicate(driver):
            try:
                page_text = WebDriverWait(driver, self.page_refresh_time).until(EC.presence_of_element_located(
                    (By.CLASS_NAME, 'pagination-item-active'))).text
                if int(page_text) == page:
                    return True
                else:
                    return False
            except StaleElementReferenceException:
                return True

        return predicate

    @property
    def next_page_element(self):
        return 1

    def goto_next_page(self):
        element = self.driver.find_element_by_class_name("pagination-next")
        self.click_link(element)

    def crawl_curr_page(self):
        for i in range(self.number_of_orders):
            self.crawl_order(i)

    @property
    def number_of_orders(self):
        return len(self.driver.find_elements_by_xpath(
            "//div[@id='sold_container']//div[contains(@class, 'item-mod__trade-order___2LnGB')]"))

    def crawl_order(self, index):
        print("\n")
        print(str(self.current_page) + "  order" + str(index))
        new_order_crawler = OrderCrawler(self.driver, index, self.data_manager)
        new_order_crawler.start()
