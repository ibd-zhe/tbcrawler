from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from Pages.page import Page
from datetime import datetime
from Util.Model import Cache, alphanum
import time

force_ship_period = 29
exit_state = ['卖家已发货', '交易成功']
no_print = ['一起发', '不拆', '跟', '并单']
itemidlist = [522670827437, 45388387252, 520080125216]


class PrintUser(Page):
    def __init__(self, driver, index, db_manager):
        super().__init__(driver)
        self.index = index
        self.db_manager = db_manager
        self.users_xpaths = "//div[@id='J_Grid']/div/div[@class='bui-grid-body']/table/tbody/tr[contains(@class, " \
                            "'bui-grid-row')]"
        self.user_xpath = self.users_xpaths + "[{0}]".format(self.index + 1)
        self.items_xpaths = self.user_xpath + "/following-sibling::tr[1]/td/table/tbody/tr[1]/td/div/table/tbody/tr"

    def __enter__(self):
        self.collapse_info()
        print('userid ' + self.user_tbid)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(exc_type)
            print(exc_val)

    def collapse_info(self):
        WebDriverWait(self.driver, 7).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, 'bui-ext-mask')))
        WebDriverWait(self.driver, 5).until(self.clickable(self.user_xpath + "/td[2]/div//i"))

        self.wait(self.user_xpath + "/td[2]/div/span[@class='bui-grid-cascade bui-grid-cascade-expand']")
        # self.wait(self.user_xpath + "/td[2]/div/span[@class='bui-grid-cascade']")

    def wait_load(self):
        WebDriverWait(self.driver, 7).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, 'bui-ext-mask')))
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '下一页')]")))
        WebDriverWait(self.driver, 10).until(self.loading())

    def loading(self):
        def predicate(driver):
            try:
                driver.find_element_by_class_name('bui-ext-mask')
            except NoSuchElementException:
                return True
            else:
                print('find bui ext mask')
                return False

        return predicate

    def clickable(self, xpath):
        def predicate(driver):
            try:
                self.click_link(WebDriverWait(driver, 7).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))))
            except WebDriverException:
                return False
            else:
                return True

        return predicate

    def start(self):
        if self.is_refunded:
            print("refund")
        elif self.printed:
            print('already printed')
        else:
            if len([i for i in self.items_response if i['state'] in exit_state]) == 0:
                if len([i for i in self.items_response if i['shipable']]) == len(self.items_response):
                    if self.find_gendan(self.items_response):
                        self.selected()
                else:
                    self.process_unshiped(self.items_response)
            else:
                unshiped = [i for i in self.items_response if i['state'] not in exit_state]
                self.process_unshiped(unshiped)

    def process_unshiped(self, item_list):
        shipables = self.shipable_items(item_list)
        if len(shipables) > 0 and self.find_gendan(item_list):
            self.db_manager.rollback(len([i for i in item_list if i['avail_q'] > 0]))
            self.split(shipables)
        else:
            print('ignore')
            self.note_list(item_list)

    @property
    def printed(self):
        if self.seller_notes:
            return '打印' in self.seller_notes

    def selected(self):
        print('打印')
        self.leave_message('打印')

    def find_gendan(self, item_list):
        if self.seller_notes:
            if [i for i in no_print if i in self.seller_notes]:
                self.note_list(item_list)
                print('跟跟蛋蛋 ' + self.user_tbid)
                return False
            else:
                return True
        else:
            return True

    def note_list(self, item_list):
        message = self.message_from_color(self.message_list(item_list))
        self.leave_message(message)

    def leave_message(self, message):
        if message:
            print('leave message  ' + message)
            self.open_edit()
            self.wait(
                "//body/div[contains(@class,'bui-dialog')]//*[contains(text(),"
                "'卖家备忘')]/following-sibling::div/textarea").send_keys(
                message)
            self.find("//body/div[contains(@class,'bui-dialog')]//button[./text()='保存']").click()
            self.driver.switch_to_default_content()
            WebDriverWait(self.driver, self.element_wait_time).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'bui-message')))
            if1 = self.driver.find_element_by_xpath("//iframe[@id='TradelistIndex']")
            self.driver.switch_to_frame(if1)
            self.close_edit()

    def message_list(self, item_list):
        return [[i['color'], i['avail_q'], i['quantity']] for i in item_list if i['avail_q'] > 0]

    def message_from_color(self, item_list):
        message = ''
        for index, i in enumerate(item_list):
            if [j for j in self.color_info_from_seller_note if j['color'].upper() in i[0].upper()]:
                continue
            if i[1] > 0:
                tmp_m = self.color_format(i[0], i[1])
                if index == len(item_list) - 1:
                    message += tmp_m
                else:
                    message += tmp_m + '<br>'

        return message

    def color_format(self, color, q):
        if q == 1:
            return '[' + color + ']'
        else:
            return '[' + color + '#' + str(q) + ']'

    # all item is 等待卖家发货
    def shipable_items(self, item_list):
        good_list = [i for i in item_list if i['shipable']]
        if len(good_list) == len(item_list):
            return [i['index'] for i in item_list]
        else:
            bad_list = [i for i in item_list if not i['shipable']]
            if sum([i['quantity'] * i['px'] for i in good_list]) > 50 and sum(
                    [i['quantity'] * i['px'] for i in bad_list]) \
                    > 50 and sum([i['quantity'] for i in good_list]) > 1 and sum([i['quantity'] for i in good_list]) \
                    > 1:
                return [i['index'] for i in good_list]
            else:
                if [i for i in good_list if i['overdue']] and not (sum([i['px'] for i in bad_list]) < 50 and sum([i['quantity'] for i in bad_list]) <= 2):
                    print('uuu')
                    return [i['index'] for i in good_list]
                else:
                    return []

    @Cache
    def items_response(self):
        if self.is_merged:
            print('merged')
            overdue = 'UnKnown'
        else:
            overdue = self.overdue
        r = []
        for itemindex in range(self.item_number):
            xpth = self.items_xpaths + "[{0}]".format(itemindex + 1)
            item_r = UserItem(self.driver, xpth, self.db_manager, overdue, self.color_info_from_seller_note).response
            item_r['index'] = itemindex
            r.append(item_r)
        print(r)
        return r

    @Cache
    def seller_notes(self):
        try:
            return self.find(
                self.user_xpath + "/following-sibling::tr[1]/td/table/tbody/tr[2]//table//tr[contains(.,"
                                  "'备忘')]/td[2]").text
        except NoSuchElementException:
            return None

    @Cache
    def color_info_from_seller_note(self):
        ttt = self.seller_notes
        if ttt:
            if not self.is_newform(ttt):
                return self.processdao(ttt)
            else:
                return self.process_color_new(ttt)
        else:
            return []

    def process_color_new(self, text):
        color_start = [index for index, i in enumerate(text) if i == '[']
        color_end = [index for index, i in enumerate(text) if i == ']']
        color_pos = [(color_start[i], color_end[i]) for i in range(len(color_start))]
        colors = []
        for i, j in color_pos:
            sp = text[i + 1: j].split('#')
            aln_color = alphanum(sp[0])
            if len(sp) > 1:
                colors.append({'color': aln_color, 'q': sp[1]})
            else:
                colors.append({'color': aln_color, 'q': 1})
        dao_txt = ''
        for index, i in enumerate(color_start):
            if index == 0:
                dao_txt += text[:i]
            else:
                dao_txt += text[color_end[index - 1]:i]

        colors.extend(self.processdao(dao_txt))
        return colors

    def processdao(self, text):
        splited_txt = text.split('到')
        if len(splited_txt) > 1:
            return [{'color': alphanum(i), 'q': 1} for i in splited_txt[:-1]]
        else:
            return []

    def is_newform(self, text):
        return '[' in text and ']' in text

    def split(self, indexlist):
        print('split')
        for index in indexlist:
            self.split_item(index)
        self.confirm_split()
        self.wait_load()
        time.sleep(5)

        with PrintUser(self.driver, self.index, self.db_manager) as u:
            return u.start()

    def confirm_split(self):
        self.find(self.confirm_split_xpath).click()

    @property
    def confirm_split_xpath(self):
        return self.user_xpath + "/following-sibling::tr[1]/td/table/tbody/tr[1]/td/div/table/thead/tr/th[10]//button"

    def split_item(self, index):
        self.find(self.split_xpath(index)).click()
        WebDriverWait(self.driver, self.element_wait_time).until(self.split_clicked(index))

    def split_clicked(self, index):
        def predicate(driver):
            if self.find(self.split_xpath(index)).text == '取消折分':
                return True
            else:
                return False

        return predicate

    def split_xpath(self, index):
        return self.items_xpaths + "[{0}]".format(index + 1) + "/td[10]//p[@title='拆分商品']"

    @property
    def item_number(self):
        return len(self.find_many(self.items_xpaths))

    @property
    def order_datetext(self):
        txt = self.find(self.user_xpath + "/td[13]").text
        return '2016-' + txt

    @property
    def overdue(self):
        order_txt = self.order_datetext
        try:
            order_date = datetime.strptime(order_txt.split(' ')[0], '%Y-%m-%d')
        except ValueError:
            return False
        else:
            return (datetime.now() - order_date).days >= force_ship_period

    @property
    def is_refunded(self):
        return 'bui-grid-row-refund' in self.find(self.user_xpath).get_attribute('class')

    @property
    def note(self):
        return self.find(self.user_xpath + "/td[6]").text

    @property
    def is_merged(self):
        return '合' in self.note

    @property
    def user_tbid(self):
        return self.find(self.user_xpath + "/td[3]").text

    def close_edit(self):
        self.find("//body/div[contains(@class,'bui-dialog')]//button[./text()='关闭']").click()
        WebDriverWait(self.driver, self.page_refresh_time).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, 'bui-dialog-editor')))

    def open_edit(self):
        self.find(self.user_xpath + "/td[15]//*[contains(text(),'编辑')]").click()
        WebDriverWait(self.driver, self.page_refresh_time).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'bui-dialog-editor')))


class UserItem(Page):
    def __init__(self, driver, xpth, data_manager, overdue, note_color_list):
        super().__init__(driver)
        self.data_manager = data_manager
        self._overdue = overdue
        self.xpth = xpth
        self.note_color_list = note_color_list

    # API
    @property
    def response(self):
        if self.state == '交易成功' or self.state == '卖家已发货':
            return {'state': self.state}
        else:
            return {
                'shipable': self.shipable,
                'px': self.unit_px,
                'overdue': self.overdue,
                'quantity': self.quantity,
                'avail_q': self.available_q,
                'state': self.state,
                'color': self.color
            }

    # Item Computed Property (Based on Business rules)
    @property
    def shipable(self):
        if self.itemid in itemidlist:
            if self.available_q >= self.quantity:
                return True
            else:
                return False
        elif self.in_stock:
            return True
        elif self.is_sample:
            return True
        elif self.in_note:
            return True
        else:
            return False

    @property
    def in_note(self):
        alphanum_color = alphanum(self.color).upper()
        alphanum_title = alphanum(self.title).upper()

        if [i for i in self.note_color_list if i['color'].upper() in alphanum_color or i['color'].upper() in
                alphanum_title]:
            return True
        else:
            return False

    @property
    def is_sample(self):
        return '分装' in self.title

    @property
    def in_stock(self):
        return '现货' in self.color or '现货' in self.title

    @property
    def overdue(self):
        if self._overdue == 'UnKnown':
            self._overdue = (datetime.now() - self.order_date).days >= force_ship_period
        return self._overdue

    # Item Crawled Property (Based on internet)
    @Cache
    def state(self):
        return self.find(self.xpth + "/td[4]/div/span/p[2]").text

    @Cache
    def tsc(self):
        txt = self.title
        tsc_txt = self.find(self.xpth + "/td[7]").text
        if tsc_txt != txt:
            return tsc_txt

    @Cache
    def title(self):
        return self.find(self.xpth + "/td[6]").text

    @Cache
    def itemid(self):
        txt = self.find(self.xpth + "/td[6]//a").get_attribute('href')
        return int(txt[36:])

    @Cache
    def color(self):
        txt = self.find(self.xpth + "/td[8]").text
        return txt.split('  ')[0]

    @Cache
    def quantity(self):
        return int(self.find(self.xpth + "/td[9]/div/span/p").text)

    @Cache
    def ordernumber(self):
        ordernumber = int(self.find(self.xpth + "/td[4]/div/span/p").text)
        return ordernumber

    @property
    def check_info(self):
        return {
            'color': self.color,
            'itemid': self.itemid,
            'tsc': self.tsc,
            'q': self.quantity
        }

    # Item Property From DataBase
    @Cache
    def order_date(self):
        return self.data_manager.date_of_order(self.ordernumber)

    @Cache
    def px_qu(self):
        return self.data_manager.check_pq(self.check_info)

    @property
    def available_q(self):
        return self.px_qu[1]

    @property
    def unit_px(self):
        return self.px_qu[0]
