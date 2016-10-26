from selenium import webdriver


from Pages.taobao.ibd.ibd_data_crawl.SellerItem import SellingItem, EditItem

a = webdriver.Chrome()
b = SellingItem(a,1)
b.prepare()

"//div[@id='J_Grid']/div/div[@class-grid-body']//tbody/tr[contains(@class,'bui-grid-row')][1]/following-sibling::tr[" \
"1]/td//tbody/tr[1]/td[6]"

