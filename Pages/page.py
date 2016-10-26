from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from selenium.webdriver.common.by import By


class Page:
    def __init__(self, driver, title_key=None, url=None):
        self.driver = driver
        self.title_key = title_key
        self.element_wait_time = 2
        self.page_refresh_time = 3
        self.open_tab_time = 3
        self.url = url

    def land_by_url(self):
        self.driver.get(self.url)

    def check_title(self):
        return WebDriverWait(self.driver, self.element_wait_time).until(EC.title_contains(self.title_key))

    def close_tab(self):
        now_index = self.window_index
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[now_index - 1])

    def click_link(self, link):
        ActionChains(self.driver).move_to_element(link).click(link).perform()

    def send_keys(self, input_element, content):
        ActionChains(self.driver).move_to_element(input_element).send_keys(content)

    def open_tab(self, link, delay=None):
        now_index = self.window_index
        self.click_link(link)
        if delay:
            sleep(delay)
        WebDriverWait(self.driver, self.open_tab_time).until(self.found_window(now_index + 1))

    def wait_click(self, xpath):
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))

    @property
    def window_index(self):
        return len(self.driver.window_handles) - 1

    def found_window(self, window_index):
        def predicate(driver):
            try:
                driver.switch_to.window(driver.window_handles[window_index])
            except IndexError:
                return False
            else:
                return True

        return predicate

    def wait(self, xpath):
        return WebDriverWait(self.driver, self.element_wait_time).until(EC.presence_of_element_located(
            (By.XPATH, xpath)))

    def find(self, xpath):
        return self.driver.find_element_by_xpath(xpath)

    def find_many(self, xpath):
        return self.driver.find_elements_by_xpath(xpath)


class MultiPage(Page):
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
