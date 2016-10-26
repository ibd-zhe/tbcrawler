import uuid

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Pages.page import MultiPage, Page
from Pages.taobao.tbcrawler import TBCrawler


class SellingItem(MultiPage):
    def __init__(self, driver, data_manager):
        super().__init__(driver)
        self.data_manager = data_manager

    def prepare(self):
        tb = TBCrawler(self.driver)
        tb.goto_sellings()

    def crawl_curr_page(self):
        for i in range(self.items_number):
            self.crawl_item(i)

    def check_pagenumber(self):
        print(self.current_page)
        WebDriverWait(self.driver, self.page_refresh_time).until(self.page_equal_to(self.current_page))

    def page_equal_to(self, page):
        def predicate(driver):
            try:
                page_text = WebDriverWait(driver, self.page_refresh_time).until(EC.presence_of_element_located(
                    (By.CLASS_NAME, 'curr-page'))).text
                if page_text == str(page):
                    return True
                else:
                    return False
            except StaleElementReferenceException:
                return True

        return predicate

    @property
    def next_page_element(self):
        try:
            self.driver.find_element_by_class_name("next-page")
            return True
        except NoSuchElementException:
            return False

    def goto_next_page(self):
        element = self.driver.find_element_by_class_name("next-page")
        self.click_link(element)

    @property
    def items_number(self):
        number = len(self.driver.find_elements_by_xpath("//div[@id='goods-on-sale']//tbody[@class='data']/tr")) / 2
        print("this page has " + str(number) + " items")
        return int(number)

    def crawl_item(self, index):
        print("page " + str(self.current_page) + "item " + str(index))
        title = self.get_item_title(index)
        tbid = self.get_item_tbid(index)
        cid = self.get_item_cid(index)
        shopid = 72076881
        data = {'item': {'title': title, 'itemid': tbid, 'cid': cid, 'shopid': shopid, 'brand': None}, 'skus': None}

        item_data_manager = self.data_manager(data=data)
        item_data_manager.write_tbitem()
        if not item_data_manager.if_has_tsc:
            detail = self.get_item_detail(index, tbid, title)
            brand = detail['brand']
            item_data_manager.item['brand'] = brand
            skus = detail['skus']
            item_data_manager.skus = skus
            item_data_manager.write_detail()
        item_data_manager.commit_db()
        print("")

    def get_item_title(self, index):
        return self.driver.find_elements_by_xpath(
            "//tbody[@class='data']/tr")[index * 2 + 1].find_element_by_xpath(
            ".//a[@class='item-title']").text

    def get_item_tbid(self, index):
        return int(self.driver.find_elements_by_xpath(
            "//tbody[@class='data']/tr")[index * 2].find_element_by_xpath(
            ".//input[@class='selector']").get_attribute('itemids'))

    def get_item_cid(self, index):
        info = self.driver.find_elements_by_xpath(
            "//tbody[@class='data']/tr")[index * 2 + 1].find_element_by_xpath(
            ".//img[@class='J_QRCode']").get_attribute(
            'data-param')
        k = 'cid='
        before_pos = info.find(k)
        after_pos = info[before_pos:].find('&')
        return int(info[before_pos:][len(k):after_pos])

    def get_item_detail(self, index, itemid, title):
        edit = self.driver.find_elements_by_xpath(
            "//tbody[@class='data']/tr")[index * 2 + 1].find_element_by_link_text('编辑宝贝')
        self.open_tab(edit)
        edit_crawler = EditItem(self.driver, itemid, title=title, validate_tsc=self.data_manager().validate_tsc)
        return edit_crawler.data


"""
目的1:
1 看是否有brand,如果没有,返回{None, None}
2 看是否有多种颜色,如果没有:
        看是否有单个tsc, 如果没有:
             返回 {None, None}
- 找tb_brand
- 看是否有多种颜色(sku):
   1 若有,爬每个颜色的信息:颜色名字, tsc, upc, 价格, 量
   2 若无(那么就只有一个款式),找出这个的tsc, upc, 价格, 量
- 如果生成了新的tsc,那么要commit
- 如果commit成功,那么返回正常值

- 找tsc时,
  1 若有,直接记录
  2 若无,生成一个和db不重复的,然后insert,
"""


class EditItem(Page):
    def __init__(self, driver, itemid, title=None, validate_tsc=None):
        super().__init__(driver)
        self.itemid = itemid
        self.title = title
        self.validate_tsc = validate_tsc
        self.edited = False
        self.response = {'brand': None, 'skus': []}

    @property
    def data(self):
        try:
            self.check_page()
        except TimeoutException:
            print("wrong page for item: " + str(self.itemid))

        else:
            brand = self.tb_brand
            if brand is None:
                print("no brand for item: " + str(self.itemid))
            self.response['brand'] = brand
            self.do_sku_job()
        finally:
            if self.edited:
                self.submit()
            self.close_tab()
            return self.response

    def do_sku_job(self):
        color_tsc_number = self.color_tsc_number
        if color_tsc_number > 0:
            info = self.skus_color_info(color_tsc_number)
            self.response['skus'] = info
        else:
            single_tsc = self.single_tsc
            if single_tsc:
                self.response['skus'] = single_tsc
            else:
                print("tsc not find for item: " + str(self.itemid))

    def submit(self):
        submit = self.driver.find_element_by_id('commit').find_element_by_tag_name('button')
        ActionChains(self.driver).move_to_element(submit).click(submit).perform()
        try:
            WebDriverWait(self.driver, self.page_refresh_time).until(EC.title_contains(self.title))
        except TimeoutException:
            pass

    def check_page(self):
        WebDriverWait(self.driver, self.element_wait_time).until(self.page_has_keyword())

    def page_has_keyword(self):
        def predicate(driver):
            if WebDriverWait(driver, self.page_refresh_time).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='page']/div[@id='main']/h1"))).text == '1. 宝贝基本信息':
                return True
            else:
                return False

        return predicate

    @property
    def tb_brand(self):
        try:
            brand = WebDriverWait(self.driver, self.element_wait_time).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//div[@id='itemBasic']//*[./text()='宝贝属性']/parent::td/following-sibling::td//*[./text("
                     ")='品牌']/parent::td/following-sibling::td//div[@class='clearfix fl']//input"))).get_attribute(
                'oldval')
        except TimeoutException:
            pass
        else:
            return brand

    @property
    def color_tsc_number(self):
        try:
            number = len(WebDriverWait(self.driver, self.element_wait_time).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[@class='sku']//tbody/tr")))) - 1
        except TimeoutException:
            return 0
        else:
            return number

    def fill_skus(self, number):
        for i in range(number):
            self.response['skus'].append({'color': self.get_sku_color(i),
                                          'px': self.get_sku_px(i),
                                          'quantity': self.get_sku_quantity(i),
                                          'tsc': self.get_sku_tsc(i),
                                          'upc': self.get_sku_upc(i)}
                                         )

    def skus_color_info(self, number):
        info = []
        for i in range(number):
            info.append({'color': self.get_sku_color(i),
                         'px': self.get_sku_px(i),
                         'quantity': self.get_sku_quantity(i),
                         'tsc': self.get_sku_tsc(i),
                         'upc': self.get_sku_upc(i)}
                        )
        return info

    def get_sku_color(self, index):
        color = self.driver.find_elements_by_xpath(
            "//div[@class='sku']//tbody/tr")[index + 1].find_elements_by_tag_name('td')[0]
        assert color.get_attribute('data-id').find('color') != -1, "Color Xpath Changed"
        return color.text

    def get_sku_px(self, index):
        return float(self.driver.find_elements_by_xpath(
            "//div[@class='sku']//tbody/tr")[index + 1].find_element_by_xpath(
            ".//input[@sku_name='price']").get_attribute('value'))

    def get_sku_quantity(self, index):
        return int(self.driver.find_elements_by_xpath(
            "//div[@class='sku']//tbody/tr")[index + 1].find_element_by_xpath(
            ".//input[@sku_name='quantity']").get_attribute('value'))

    def get_sku_tsc(self, index):
        tsc = self.driver.find_elements_by_xpath(
            "//div[@class='sku']//tbody/tr")[index + 1].find_element_by_xpath(
            ".//input[@sku_name='outerId']").get_attribute('value')
        new_tsc = self.validate_tsc(tsc)
        if index > 0:
            new_tsc = self.internal_validate_tsc(new_tsc)

        if tsc != new_tsc:
            self.insert_tsc(index, new_tsc)
            self.edited = True
        return new_tsc

    def internal_validate_tsc(self, tsc):
        all_tscs = [i['tsc'] for i in self.response['skus']]
        if tsc not in all_tscs:
            return tsc
        else:
            return self.add_tsc(tsc)

    def add_tsc(self, tsc):
        return tsc + uuid.uuid4().hex[:4]

    def insert_tsc(self, index, new_tsc):
        self.driver.find_elements_by_xpath(
            "//div[@class='sku']//tbody/tr")[index + 1].find_element_by_xpath(
            ".//input[@sku_name='outerId']").clear()
        self.driver.find_elements_by_xpath(
            "//div[@class='sku']//tbody/tr")[index + 1].find_element_by_xpath(
            ".//input[@sku_name='outerId']").send_keys(new_tsc)

    def get_sku_upc(self, index):
        try:
            return self.driver.find_elements_by_xpath(
                "//div[@class='sku']//tbody/tr")[index + 1].find_element_by_xpath(
                ".//input[@sku_name='barcode']").get_attribute('value')
        except NoSuchElementException:
            return None

    @property
    def single_tsc(self):
        try:
            tsc_element = WebDriverWait(self.driver, self.element_wait_time).until(
                EC.presence_of_element_located(
                    (By.XPATH, self.single_xpath('new') + "//input[@id='outerId")))
        except TimeoutException:
            try:
                only_tsc = self.driver.find_element_by_id('outerIdId')
            except NoSuchElementException:
                pass
            else:
                return [{
                    'tsc': only_tsc.get_attribute('value'),
                    'px': self.single_px('old'),
                    'quantity': self.single_quantity('old')
                }]
        else:
            return [{
                'tsc': tsc_element.get_attribute('value'),
                'px': self.single_px('new'),
                'upc': self.single_upc,
                'quantity': self.single_quantity('new')
            }]

    def single_px(self, version):
        return float(self.driver.find_element_by_xpath(
            self.single_xpath(version) + self.single_px_xpath(version)).get_attribute('value'))

    def single_quantity(self, version):
            return int(self.driver.find_element_by_xpath(
                self.single_xpath(version) + self.singe_q_xpath(version)).get_attribute('value'))

    @property
    def single_upc(self):
        try:
            upc = WebDriverWait(self.driver, self.element_wait_time).until(
                EC.presence_of_element_located(
                    (By.XPATH, self.single_xpath('new') + "//input[@id='barcode")))
        except TimeoutException:
            pass
        else:
            return upc.get_attribute('value')

    def single_xpath(self, version):
        if version == 'new':
            return "//table[@class='price-table']/tbody/tr"
        else:
            return "//ur[@id='J_form']"

    def single_px_xpath(self, version):
        if version == 'new':
            return "//input[@id='price']"
        else:
            return "//li[@id='fixpriceOption2']//input"

    def singe_q_xpath(self, version):
        if version == 'new':
            return "//input[@id='quantity']"
        else:
            return "//input[@id='quantityId']"

    def single_tsc_xpath(self, version):
        if version == 'new':
            return "//input[@id='outerId']"
        else:
            return "//input[@id='outerIdId']]"

    def single_upc_xpath(self, version):
        if version == 'new':
            return "//input[@id='barcode']"
        else:
            return None
