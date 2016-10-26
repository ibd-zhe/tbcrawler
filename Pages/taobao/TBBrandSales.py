import sys
import time

import psycopg2
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Pages.taobao.itemdetail import TBCrawler, ItemDetailCrawler

# 品牌有两个拼写,一个是淘宝的品牌名,一个是搜索此品牌时该打的字母(按品牌名有时会搜到不相关的品牌)

item_section = ['auctions', 'personalityData']


def ring(n):
    a = 0
    while a < n:
        sys.stdout.write('\a')
        sys.stdout.flush()
        a += 1


class BrandSalesCrawler(TBCrawler):
    def __init__(self, brand, date):
        super().__init__()
        self.brand = brand

        self.crawl_date = date
        self.dbinfo = "dbname='tbbrandsales' user='jiangjiang' host='localhost' password='8326022'"
        # list of dictionary {price, tbupc, volume, category}

        self.search_name, self.tb_brand, self.gabage_brand = self.get_brand_info()

        # list of dictionary {tbupc, brand}
        self.data = []
        self.wrong_data = []
        self.already_data = self.get_already_data()
        self.stop = False

    def get_brand_info(self):
        con = psycopg2.connect(self.dbinfo)
        cur = con.cursor()
        cur.execute("""SELECT tb_search_term, tb_name, tb_not_name FROM brand WHERE name=%s;""", (self.brand,))
        d = cur.fetchall()
        search = d[0][0]
        br = d[0][1].split(';;')
        if d[0][2]:
            bc = d[0][2].split(';;')
        else:
            bc = []
        return search, br, bc

    def get_already_data(self):
        con = psycopg2.connect(self.dbinfo)
        cur = con.cursor()
        cur.execute(
            """SELECT itemid FROM sales WHERE time=%s and itemid IN (SELECT itemid FROM item WHERE brand=%s);""",
            (self.crawl_date, self.brand))
        d = [i[0] for i in cur.fetchall()]
        con.close()
        print(str(len(d)) + " already crawled")
        return set(d)

    def start(self):
        self.search_brand()
        self.crawl_items()

        while not self.is_final_page() and not self.stop:
            self.goto_next_page()
            time.sleep(3)
            self.crawl_items()

        print("done")

    def search_brand(self):
        self.login()
        time.sleep(3)
        self.home_search(self.search_name)
        self.filter_category()
        time.sleep(3)
        self.filter_rank()
        time.sleep(3)

    def filter_category(self):
        WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located((By.XPATH, "//a[@title='彩妆/香水/美妆工具']"))).click()

    def filter_rank(self):
        WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located((By.XPATH, "//li[@class='sort']/a[@trace='sortSaleDesc']"))).click()

    def is_final_page(self):
        try:
            self.driver.find_element_by_css_selector('.item.next.next-disabled')
            return True
        except NoSuchElementException:
            return False

    def crawl_items(self):
        print(self.get_pages())
        for i in item_section:
            print(i)
            if not self.stop:
                self.crawl_section(i)
            else:
                break

        self.write_data()

    def write_data(self):
        con = psycopg2.connect(self.dbinfo)
        cur = con.cursor()
        for i in self.data:
            i['brand'] = self.brand
            i['time'] = self.crawl_date
        try:
            cur.executemany(
                """INSERT INTO item(itemid, categoryid, brand) VALUES (%(tbupc)s, %(category)s, %(brand)s);""",
                self.data
            )
        except psycopg2.IntegrityError as ie:
            con.rollback()
            new_cid = self.find_new_cid(str(ie))
            cur.execute("""INSERT INTO category (categoryid) VALUES(%s);""", (new_cid,))
            print("insert new cid " + str(new_cid))
            con.commit()
            con.close()
            self.write_data()
        else:
            cur.executemany(
                """INSERT INTO sales(itemid, price, volume, time) VALUES (%(tbupc)s, %(price)s, %(volume)s, %(time)s);""",
                self.data
            )
            con.commit()
            con.close()
            self.data = []
            print(self.wrong_data)

    def find_new_cid(self, ie):
        pre_str = 'Key (categoryid)=('
        start_pos = ie.find(pre_str)
        after_pos = ie[start_pos + len(pre_str):].find(')')
        return int(ie[start_pos + len(pre_str):][:after_pos])

    def crawl_section(self, section):
        try:
            items = len(self.get_item_elements(section))
        except TimeoutException:
            print("no " + section)
            return

        for i in range(items):
            if not self.stop:
                print(str(i) + "/" + str(range(items)))
                self.crawl_single_item(self.get_item_xpath(i, section))
            else:
                return

    def get_item_elements(self, section):
        return WebDriverWait(
            self.driver, 3).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@class='items']//div[@data-category='{0}']".format(section))))

    def crawl_single_item(self, item):
        # 在搜索页看到的宝贝交易数量,因为是按数量由大到小排序,因此如果到0,即可终止程序
        outer_volume = self.get_item_outer_volume(item)
        if outer_volume == 0:
            self.stop = True
            return

        # 如果之前已经爬过这个宝贝,skip
        tbupc = self.get_item_tbupc(item)
        if tbupc in self.already_data:
            print("already crawled: " + str(tbupc))
            return

        price = self.get_item_price(item)
        detail = self.get_item_detail(item)

        if detail:
            brand = detail[0]
            category = detail[1]
            volume = detail[2]
            if brand in self.tb_brand:
                self.data.append({'category': category, 'price': price, 'volume': volume, 'tbupc': tbupc})
                print("宝贝" + str(tbupc) + ", 第" + str(len(self.data)) + "个, " + str(volume) + "人购买")
            else:
                if brand in self.gabage_brand:
                    self.wrong_data.append({'tbupc': tbupc, 'reason': "wrong brand: " + brand})
                    print("错误品牌: " + brand)
                else:
                    ring(15)
                    if input("add brand: " + brand + " to database?") == 'yes':
                        self.insert_brand_db(brand)
                        self.data.append({'category': category, 'price': price, 'volume': volume, 'tbupc': tbupc})
                        print("宝贝" + str(tbupc) + ", 第" + str(len(self.data)) + "个, " + str(volume) + "人购买")
                    else:
                        self.insert_gabage_brand(brand)
                        self.wrong_data.append({'tbupc': tbupc, 'reason': "wrong brand: " + brand})
                        print("错误品牌: " + brand)

        else:
            self.wrong_data.append({'tbupc': tbupc, "reason": "miss detail"})
            print("miss detail: " + str(tbupc))

    def insert_gabage_brand(self, gabage):
        con = psycopg2.connect(self.dbinfo)
        cur = con.cursor()
        self.gabage_brand.append(gabage)
        new_tb_not_name = ';;'.join(self.gabage_brand)
        cur.execute("""UPDATE brand SET tb_not_name=%s WHERE name=%s;""", (new_tb_not_name, self.brand))
        con.commit()
        con.close()

    def insert_brand_db(self, brand):
        con = psycopg2.connect(self.dbinfo)
        cur = con.cursor()
        self.tb_brand.append(brand)
        new_tb_name = ";;".join(self.tb_brand)
        cur.execute("""UPDATE brand SET tb_name=%s WHERE name=%s;""", (new_tb_name, self.brand))
        con.commit()
        con.close()

    def get_item_tbupc(self, item_xpath):
        return int(WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, item_xpath + "//div[@class='shop']/a"))).get_attribute('data-nid'))

    def get_item_detail(self, item_xpath):

        item_link = WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, item_xpath + "//a[@class='J_ClickStat']")))

        self.open_tab(item_link)
        item_detail_crawler = ItemDetailCrawler(self.driver)
        item_detail = item_detail_crawler.get_attributes()
        self.close_tab()
        return item_detail

    def get_item_price(self, item_xpath):
        price_text = WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, item_xpath + "//div[@class='price g_price g_price-highlight']"))).text

        return float(price_text[1:])

    def get_item_outer_volume(self, item_xpath):
        volume_text = WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, item_xpath + "//div[@class='deal-cnt']"))).text

        return self.find_number_in_string(volume_text)

    def find_number_in_string(self, string):
        start = 0
        end = 0
        for i in range(len(string) - 1):
            if string[i].isdigit():
                start = i
                break

        for i in range(len(string) - 1, -1, -1):
            if string[i].isdigit():
                end = i
                break

        return int(string[start:end + 1])

    def get_item_xpath(self, index, section):
        return "//div[@class='items']//div[@data-index='{0}'][@data-category='{1}']".format(index, section)

    def goto_next_page(self):
        print("next page")
        next_page_link = self.driver.find_element_by_css_selector('.item.next')
        ActionChains(self.driver).move_to_element(next_page_link).click(next_page_link).perform()

    def get_pages(self):
        page_text = self.driver.find_element_by_class_name('current').find_element_by_xpath('..').text
        return page_text

    def goto_page(self, page_number):
        WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='mainsrp-pager']//input")
            )
        ).send_keys(page_number)

        WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='mainsrp-pager']//div[@class='form']/span[@class='btn J_Submit']")
            )
        ).click()
        time.sleep(5)


if __name__ == '__main__':
    aaaa = BrandSalesCrawler(sys.argv[1], sys.argv[2])
    aaaa.start()
