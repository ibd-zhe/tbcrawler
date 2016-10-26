from datetime import datetime
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Pages.taobao.tbcrawler import TBCrawler


class OrderCrawler:
    def __init__(self, driver, index, data_manager=None):
        self.driver = driver
        self.orderindex = index
        self._orderxpath = None
        self.data_manager = data_manager
        self._items = []
        self.element_wait_time = 3
        self.mission = None
        self._order_number = None
        self._itemsnumber = None

    @property
    def orderxpath(self):
        if self._orderxpath is None:
            self._orderxpath = \
                "//div[@id='sold_container']//div[contains(@class,'item-mod__trade-order___2LnGB')][{0}]".format(self.orderindex + 1)
        return self._orderxpath

    def start(self):
        ordernumber = self.order_number
        item_num_db = self.data_manager.check_ordernumber(ordernumber)
        item_num = self.order_item_number

        if item_num_db < item_num:
            self.mission = 'insert'
        else:
            self.mission = 'update'
        print(self.mission)
        self.data_manager.start({'mission': self.mission, 'data': self.response})

    @property
    def response(self):
        if self.mission == 'insert':
            return {
                'items': self.items,
                'order_time': self.order_time,
                'number': self.order_number,
                'user_id': self.order_userid,
                'state': self.order_state,
                'total': self.order_total,
            }
        elif self.mission == 'update':
            return {
                'items': self.items,
                'number': self.order_number,
                'state': self.order_state
            }

    @property
    def order_number(self):
        if self._order_number is None:
            self._order_number = int(WebDriverWait(
                self.driver, self.element_wait_time).until(
                EC.presence_of_element_located((By.XPATH, self.orderxpath + "//tbody[1]/tr/td[1]//span[3]"))
            ).text)
            print(self._order_number)
        return self._order_number

    @property
    def order_userid(self):

        return WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located((By.XPATH, self.items[0]['xpath'] + "/td[5]"))
        ).text

    @property
    def order_state(self):
        state_text = WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located((By.XPATH, self.items[0]['xpath'] + "/td[6]"))
        ).text
        state = state_text.split('\n')[0]
        assert state != '', "state is empty"
        return state

    @property
    def order_total(self):
        px = WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, self.items[0]['xpath'] + "/td[7]//*[contains(text(),'￥')]/following-sibling::span"))
        ).text
        return float(px)

    @property
    def order_time(self):
        time_text = WebDriverWait(
            self.driver, self.element_wait_time).until(
            EC.presence_of_element_located((By.XPATH, self.orderxpath + "//tbody[1]/tr/td[1]//span[6]"))
        ).text
        return datetime.strptime(time_text, '%Y-%m-%d %H:%M:%S')

    @property
    def items(self):
        if not self._items:
            for i in range(self.order_item_number):
                item = ItemCrawler(self.driver, i, self.orderxpath, self.data_manager, self.mission)
                self._items.append(item.response)
        return self._items

    @property
    def order_item_number(self):
        if self._itemsnumber is None:
            self._itemsnumber = len(self.driver.find_elements_by_xpath(self.orderxpath + "//table[2]/tbody/tr"))
        return self._itemsnumber


class ItemCrawler(TBCrawler):
    def __init__(self, driver, index, orderxpath, data_manager, mission):
        super().__init__(driver)
        self.index = index
        self._xpath = None
        self.orderxpath = orderxpath
        self._info = None
        self._tsc = ''
        self._title = None
        self.data_manager = data_manager
        self.insert_title = False
        self.mission = mission

    @property
    def xpath(self):
        if self._xpath is None:
            self._xpath = self.orderxpath + "//table[2]/tbody/tr[{0}]".format(self.index + 1)
        return self._xpath

    @property
    def response(self):
        if self.mission == 'insert':
            return {
                'tsc': self.tsc,
                'itemid': self.itemid,
                'color': self.color,
                'price': self.price,
                'quantity': self.quantity,
                'state': self.state,
                'title': self.title,
                'xpath': self.xpath
            }
        elif self.mission == 'update':
            return {
                'itemid': self.itemid,
                'color': self.color,
                'xpath': self.xpath,
                'state': self.state,
            }

    @property
    def quantity(self):
        return int(self.driver.find_element_by_xpath(
            self.xpath + "/td[3]").text)

    @property
    def state(self):
        return self.driver.find_element_by_xpath(
            self.xpath + "/td[4]").text

    @property
    def itemid(self):
        id_from_title = self.id_by_title
        if id_from_title:
            return id_from_title
        else:
            itemid = self.id_by_click
            if self.insert_title:
                self.data_manager.insert_title_for_item(itemid, self.title)
            return itemid

    @property
    def id_by_title(self):
        id_from_title = self.data_manager.itemid_of_title(self.title)
        if not id_from_title:
            print("no title")
            self.insert_title = True
        if isinstance(id_from_title, int):
            return id_from_title

    @property
    def id_by_click(self):
        link = self.driver.find_element_by_xpath(
            self.xpath + "//td[1]/div/div[1]/a")
        self.open_tab(link, delay=0.5)
        url = self.driver.current_url
        url_identifier = url.split('//')[1][:4]
        itemid = ''
        if url_identifier == 'item':
            id_key = 'id='
            id_pos = url.find(id_key)
            itemid = url[id_pos + len(id_key):]
        elif url_identifier == 'trad':
            itemid = self.get_id_from_tradepage()
        self.close_tab()
        return int(itemid)

    def get_id_from_tradepage(self):
        try:
            id_element = WebDriverWait(self.driver, self.element_wait_time).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), '商品ID')]"))
            )
            try:
                itemid = id_element.text.split(': ')[1]
            except IndexError:
                itemid = id_element.find_element_by_xpath(
                    "./following-sibling::span").text
        except TimeoutException:
            try:
                id_text_from_script = self.driver.find_element_by_xpath("//script[@charset='gbk']").get_attribute('src')
            except NoSuchElementException:
                if self.driver.find_element_by_xpath("//*[contains(text(),'对不起')]"):
                    self.relogin()
                    self.close_tab()
                    return self.id_by_click
            else:
                itemid = id_text_from_script.split('/')[6]
                print('fuuuuuuuuuuucku')
                return itemid
        else:
            return itemid

    @property
    def price(self):
        price_text = self.driver.find_element_by_xpath(
            self.xpath + "/td[2]").text
        return float(price_text[1:])

    @property
    def title(self):
        if self._title is None:
            self._title = self.info.split('\n')[0]
        return self._title

    @property
    def color(self):
        try:
            return self.driver.find_element_by_xpath(
                self.xpath + "/td[1]//*[contains(text(), '颜色分类')]/following-sibling::span[2]").text
        except NoSuchElementException:
            pass

    @property
    def tsc(self):
        if self._tsc == '':
            try:
                self._tsc = self.driver.find_element_by_xpath(
                    self.xpath + "/td[1]//*[contains(text(), '商家编码')]/following-sibling::span[1]").text
            except NoSuchElementException:
                self._tsc = None
        return self._tsc

    @property
    def info(self):
        if self._info is None:
            self._info = self.driver.find_element_by_xpath(self.xpath + "/td[1]").text
        return self._info
