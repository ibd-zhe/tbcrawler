from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time


class ItemDetailCrawler:
    def __init__(self, driver):
        self.driver = driver

    def get_attributes(self):
        brand = self.get_brand()
        cid = self.get_cateid()
        volume = self.get_volume()
        if brand and cid and volume:
            return brand, cid, volume
        else:
            return False

    def get_brand(self):
        try:
            brand = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//ul[@class='attributes-list']/*[contains(text(), '品牌')]"))).get_attribute('title')

        except TimeoutException:
            if not self.check_item_exist():
                return False
            if self.check404():
                self.driver.refresh()
                time.sleep(3)
                self.get_brand()
            else:
                return False
        else:
            return brand

    def get_cateid(self):
        return self.driver.execute_script('return g_config;')['idata']['item']['cid']

    # text是'30天内已售出7804件，其中交易成功5980件',我们要找到5980
    def get_volume(self):
        volume_text = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='tb-sell-counter']/a"))).get_attribute('title')

        pre_pos = volume_text.find('交易成功')
        after_pos = volume_text[pre_pos:].find('件')
        try:
            volume = int(volume_text[pre_pos:][4:after_pos])
        except ValueError:
            return False
        else:
            return volume

    def check_item_exist(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='error-notice']//*[contains(text(), '宝贝不存在')]")))
            return False
        except TimeoutException:
            return True

    def check404(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//body//*[contains(text(), '404 Not Found')]")))
            return True
        except TimeoutException:
            return False
