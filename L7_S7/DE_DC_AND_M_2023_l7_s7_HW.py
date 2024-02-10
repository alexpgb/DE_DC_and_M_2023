"""
В качестве цели для скрапинга выберем раздел с газоывыми плитами на сайте 'https://www.dns-shop.ru/'.
Сохраняем:
 - наименование
 - цену, 
 - цену с скидкой
 - url на страницу с детальной информацией
Трудности:
 - обычными средствами сайт https://www.dns-shop.ru/ не парсится, т.к. при первом переходе загружается скрипт, который анализирует 
 по браузера на предмет наличия признаков автоматизиорованного скрейпинга.
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import csv
import urllib
from pathlib import Path

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs


RESULT_FILE_NAME = 'l7_s7_t1_hw.csv'

def main():
    items_as_list = []
    while True:
        opts = uc.ChromeOptions()
        opts.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        driver = uc.Chrome(options=opts)
        driver.set_window_size(1000, 800)

        url = 'https://www.dns-shop.ru/'
        driver.get(url)

        print(driver.title)
        time.sleep(1)

        select_city_popup_webelement = driver.find_elements(By.XPATH, "//p[contains(@class, 'confirm-city')]/span[text()='Ваш город']")
        if len(select_city_popup_webelement) > 0:
            print(0)
            select_city_popup_webelement_change_city = select_city_popup_webelement[0].find_elements(By.XPATH, "//button/span[text()='Сменить город']")
            if len(select_city_popup_webelement_change_city) > 0:
                print(1, type(select_city_popup_webelement_change_city[0]))
                select_city_popup_webelement_change_city[-1].click()
        else:
            print(f'Не найден попап с переходом на выбор города')
            break

        time.sleep(1)
        city_name_input = driver.find_elements(By.XPATH, "//input[@data-city-select]")
        if len(city_name_input) > 0:
            city_name_input[0].send_keys('Екатеринбург')
            city_name_input[0].send_keys(Keys.RETURN)
        else:
            print('Не найден инпут для указания города')
            break
        
        time.sleep(1)
        catalog_popup = driver.find_elements(By.XPATH, "//div[contains(@class, 'catalog-menu') and text()='Каталог товаров']/parent::a[1]")
        if len(catalog_popup) > 0:
            print(f"{catalog_popup[0].get_attribute('href')=}")
            url_catalog = urllib.parse.urljoin(url, catalog_popup[0].get_attribute("href"))
            driver.get(url_catalog)
        else:
            print('Не найлен элемент с для перехоа в каталог товаров.')
            break

        time.sleep(1)
        catalog_subcategory_popup_item = driver.find_elements(By.XPATH, "//a[contains(@class, 'subcategory') and text()='Техника для кухни']")
        if len(catalog_subcategory_popup_item) > 0:
            print(catalog_subcategory_popup_item[0].get_attribute("href"))
            url_catalog_kitchen_tech = urllib.parse.urljoin(url, catalog_subcategory_popup_item[0].get_attribute("href"))
            driver.get(url_catalog_kitchen_tech)
        else:
            print('Не найлен элемент с для перехоа в каталог с техникой для кухни.')
            break

        time.sleep(2)
        catalog_oven = driver.find_elements(By.XPATH, "//span[contains(@class, 'subcategory') and text()='Плиты и печи']/../..")
        if len(catalog_oven) > 0:
            print(catalog_oven[0].get_attribute("href"))
            url_catalog_oven = urllib.parse.urljoin(url, catalog_oven[0].get_attribute("href"))
            driver.get(url_catalog_oven)
        else:
            print('Не найден элемент для перехода в каталог с плитами')
            break

        time.sleep(1)
        catalog_gas_oven = driver.find_elements(By.XPATH, "//span[contains(@class, 'subcategory') and text()='Плиты газовые']/../..")
        if len(catalog_gas_oven) > 0:
            print(catalog_gas_oven[0].get_attribute("href"))
            url_catalog_gas_oven = urllib.parse.urljoin(url, catalog_gas_oven[0].get_attribute("href"))
            # driver.get(url_catalog_gas_oven)
        else:
            print('Не найден элемент для перехода в каталог с газовыми плитами')
            break
        
        n = 1
        next_page_url = url_catalog_gas_oven
        while True:
            # Если в строке next_page_url не будет содержаться url cайта. По факту будет 'javascript: когда мы достигнем последней страницы
            if url not in next_page_url or \
                n >= 15 : # 15 на всякий случай если все ограничения на контент не сработают и ПО уйдет в бесконечный цикл
                break
            driver.get(next_page_url)
            print(f"Page load: {driver.current_url}")
            soup = bs(driver.page_source, 'html.parser')
            blocks_in_page = soup.find_all('div', attrs={'data-id':['product']})
            if len(blocks_in_page) == 0:
                # Закончился контент
                break
            for block in blocks_in_page:
                item = {}
                try:
                    item['name'] = block.find('a', attrs={'class': 'catalog-product__name'}).find('span').text
                except:
                    item['name'] = None
                if item['name']:
                    item['url'] = urllib.parse.urljoin(url, block.find('a', attrs={'class': 'catalog-product__name'}).get('href'))
                    try:
                        price_block = block.find('div', attrs={'class': 'product-buy__price'}).text.strip()
                    except:
                        price_block = None
                    price = None
                    price_val = None
                    price_sale = None
                    if price_block and '₽' in price_block:
                        price = price_block.split('₽')[0].split('\xa0')[0].strip().replace(' ', '')
                        price_val =  '₽'
                        if len(price_block.split('₽')) > 1:
                            price_sale = price_block.split('₽')[1].strip().replace(' ', '')
                    item['price'] = price
                    item['price_val'] = price_val
                    item['price_sale'] = price_sale
                    items_as_list.append(item)         
            next_page_url = driver.find_elements(By.XPATH, "//li[contains(@class, 'pagination-widget__page_active')]/following-sibling::li[1]/a")[0].get_attribute("href")
            n += 1        
        driver.quit()
        del driver        
        break
    print(f'Извлечено элементов: {len(items_as_list)}')
    n = 0
    if len(items_as_list) > 0:
        with open((Path(__file__).parent / RESULT_FILE_NAME), 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.DictWriter(f, fieldnames=items_as_list[0].keys())
            csv_writer.writeheader
            for item in items_as_list:
                n += 1
                csv_writer.writerow(item)    
        print(f'Сохранено элементов: {len(items_as_list)}')
        
if __name__ == '__main__':
    main()
