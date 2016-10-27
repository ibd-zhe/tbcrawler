from Pages.taobao.tbcrawler import MultiPageTBCrawler
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from Pages.taobao.ibd.print_order.orderitem import PrintUser


class PrintOrder(MultiPageTBCrawler):
    def __init__(self, driver, db_manager):
        super().__init__(driver)
        self.db_manager = db_manager
        self.element_wait_time = 5
        self.print_list = []

    def prepare(self):
        self.driver.get("http://99tp.cn")
        self.wait("//*[contains(text(),'点此登陆')]").click()
        self.wait("//*[contains(text(),'授权并登录')]").click()
        print(WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dl-selected'))).text)

        print(WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tab-nav-actived'))).text)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'bui-ext-close'))).click()
        self.switch_frame()
        self.filter()
        self.change_time_order()

    def switch_frame(self):
        if1 = self.driver.find_element_by_xpath("//iframe[@id='TradelistIndex']")
        self.driver.switch_to_frame(if1)

    def filter(self):
        self.find("//button[contains(text(), '高级')]").click()
        WebDriverWait(self.driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, "//div//div[contains(text(),'查询订单')]")))
        self.wait(
            "//div[contains(@class,'bui-dialog')]//label[contains(text(),'商品标题')]/following-sibling::div//input") \
            .send_keys('持久不脱色')
        self.wait("//div//select/option[contains(text(),'等待卖家发货')]").click()
        self.find("//div[contains(@class,'bui-dialog')]//button[contains(text(),'开始查询')]").click()
        self.wait_load()

    def change_time_order(self):
        ActionChains(self.driver).move_to_element(self.find(
            "//div[@id='J_GridOrder']//input[@class='bui-select-input']")).perform()
        ActionChains(
            self.driver).move_to_element(
            self.find(
                "//div[@id='J_GridOrder']//input[@class='bui-select-input']")).click(
            self.find(
                "//div[contains(@class,'bui-list-picker')]//ul/li[./text()='付款时间']/span[./text()='从前到后']")).perform()
        self.wait_load()

    def crawl_curr_page(self):
        for i in range(len(self.driver.find_elements_by_xpath(self.users_xpaths))):
            self.crawl_user(i)
            if len(self.print_list) >= 50:
                self.print()

    def wait_load(self):
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '下一页')]")))
        WebDriverWait(self.driver, 5).until(self.loading())

    def loading(self):
        def predicate(driver):
            try:
                driver.find_element_by_class_name('bui-ext-mask')
                print('find bui-ext-mask')
            except NoSuchElementException:
                return True
            else:
                return False
        return predicate

    def check_pagenumber(self):
        print(self.current_page)
        WebDriverWait(self.driver, self.page_refresh_time).until(self.page_equal_to(self.current_page))

    def page_equal_to(self, page):
        def predicate(driver):
            try:
                page_text = WebDriverWait(driver, self.page_refresh_time).until(EC.presence_of_element_located(
                    (By.CLASS_NAME, 'bui-pb-page'))).get_attribute('value')
                try:
                    number = int(page_text)
                except ValueError:
                    return False
                else:
                    if number == page:
                        return True
                    else:
                        return False
            except StaleElementReferenceException:
                return True
        return predicate

    def print(self):
        for i in self.print_list:
            print(i['index'], i['user_id'])
            self.select(i['index'], i['user_id'])
        print(self.db_manager.printout())
        self.wait_for_yes()
        del self.print_list[:]

    def wait_for_yes(self):
        while input("请打印, 打印完了吗?") != 'yes':
            self.wait_for_yes()

    def select(self, index, user_id):
        test_user = self.user_id_of(index)
        xpth = self.user_xpth(index)
        assert test_user == user_id, 'wrong userid: ' + test_user + ' of index: ' + str(index) + ' real user: ' + user_id
        assert self.items_printstate(index) != '已打印', '状态不是发货'
        self.click_link(self.find(xpth + "/td[1]/div/div/span"))
        WebDriverWait(self.driver, 2).until(self.selected(xpth))
        try:
            self.find(xpth + "/td[2]/div/span[@class='bui-grid-cascade bui-grid-cascade-expand']")
        except NoSuchElementException:
            self.click_link((xpth + "/td[2]/div//i"))
        finally:
            self.wait(xpth + "/td[2]/div/span[@class='bui-grid-cascade bui-grid-cascade-expand']")

    def items_printstate(self, index):
        return self.find(self.user_xpth(index) + "/td[10]").text

    def user_id_of(self, index):
        return self.find(self.user_xpth(index) + "/td[3]").text

    def selected(self, xpth):
        def predicate(driver):
            try:
                self.find(xpth + "[contains(@class, 'bui-grid-row-selected')]")
            except NoSuchElementException:
                return False
            else:
                return True

        return predicate

    def user_xpth(self, index):
        return self.users_xpaths + "[{0}]".format(index + 1)

    def crawl_user(self, i):
        print('\n')
        print(str(i) + "th user")
        with PrintUser(self.driver, i, self.db_manager) as u:
            l = u.start()
            if l['print'] is True:
                self.print_list.append(l)
            else:
                print('not print')

    @property
    def users_xpaths(self):
        return "//div[@id='J_Grid']/div/div[@class='bui-grid-body']/table/tbody/tr[contains(@class, " \
               "'bui-grid-row')]"

    def goto_next_page(self):
        self.find("//button[contains(text(), '下一页')]").click()
        self.wait_load()



