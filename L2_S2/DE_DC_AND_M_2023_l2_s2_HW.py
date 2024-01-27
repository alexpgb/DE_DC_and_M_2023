"""
Выполнить скрейпинг данных в веб-сайта http://books.toscrape.com/ и извлечь информацию о всех книгах на сайте во всех категориях:
 название, цену, количество товара в наличии (In stock (19 available)) в формате integer, описание.
Затем сохранить эту информацию в JSON-файле.
"""

import requests
from bs4 import BeautifulSoup as bs
import json
import urllib
import time
import logging
from pathlib import Path


BASE_URL = 'https://books.toscrape.com/'
RESULT_FILE_NAME = 'l2_s2_t2_hw.json'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
TIMEOUT_MILLISEC = 1000
HEADERS = {}
HEADERS['User-Agent'] = USER_AGENT
PAGE_LOAD_STATUS_OK = 1
PAGE_LOAD_STATUS_NOT_LOADED = 0
PAGE_LOAD_STATUS_ERROR = -1
PAGE_URL_START = '' # 'catalogue/page-49.html'
PAGE_PROCESS_NUM_MAX = 2 # -1 - без ограничения количества обрабатываемых страниц
EXTRACT_QUANTITY = True


logging.basicConfig(level=logging.INFO)

class RequestParams:
    def __init__(self, headers={}, params_in_query={}, params_in_body=None,):
        self.headers = headers
        self.params_in_query = params_in_query
        self.params_in_body = params_in_body

class Site:    
    """
    Моделирует сущность сайт
    """
    def  __init__(self, base_url):
        self.url = base_url

class Page:
    """
    Моделирует сущность страница с которой нужно собратьи информацию
    """
    def __init__(self, site:Site, page_url:str, params:RequestParams):
       self.site_url = site.url
       self.page_url = urllib.parse.urljoin(self.site_url, page_url)
       self.params = params
       self.page_load_status = PAGE_LOAD_STATUS_NOT_LOADED # 0 - страница не загружалась -1 ошибка загрузки страницы 1 - страница загружена успешно
       self.page_content = None
       self.responce_last_status_code = None
       self.responce_last_error_message = None

    
    def load_page_content(self):
        self.page_content = None
        resp = requests.get(self.page_url, params=self.params.params_in_query, headers=self.params.headers)
        self.responce_last_status_code = resp.status_code
        if resp.ok:
            self.page_content = resp.content
            self.page_load_status = PAGE_LOAD_STATUS_OK
        else:
            self.page_load_status = PAGE_LOAD_STATUS_ERROR 
            self.responce_last_error_message = resp.text

    def reset_page_url(self, page_url:str):
        self.page_url = urllib.parse.urljoin(self.site_url, page_url)
        self.page_load_status = PAGE_LOAD_STATUS_NOT_LOADED
        self.page_content = None
        self.responce_last_status_code = None
        self.responce_last_error_message = None


    def reset_params(self, params:RequestParams):
        self.params = params


class Scraper:
    """
    Сущность, моделирующая процесс скрейпинга страницы сайта
    """
   
    def __init__(self, page:Page) -> None:
        self.currenrt_scraped_page: Page = page
        self.next_page_url:Page = None
        self.currenrt_scraped_page_context = None ## здесь храниться путь до текущей страницы 
        ## без имени самой страницы. Это нужно для формирования ссылок на следующую страницу,
        # если ссылка на странице была относительная.
        self.soup = None

    def load_content_and_parse(self, parser='html.parser'):
        self.currenrt_scraped_page.load_page_content()
        if self.currenrt_scraped_page.page_load_status == PAGE_LOAD_STATUS_OK:
            self.currenrt_scraped_page_context = Path(urllib.parse.urlparse(self.currenrt_scraped_page.page_url).path).parent.as_posix()
            self.soup = bs(self.currenrt_scraped_page.page_content, parser)

    # def parse_page(self, parser):
    #     self.soup = bs(self.currenrt_scraped_page.page_content)

    def extract_and_set_next_page_url(self, foo):
        path = foo(self.soup)
        self.set_next_page_url(path)

    def set_next_page_url(self, path, context=None):
        if  context is not None:
            self.currenrt_scraped_page_context = context
        if  path is None: # нет ссылки на следующую страницу
            result = path
        # elif len(urllib.parse.urlparse(self.currenrt_scraped_page.page_url).path.replace('/','')) == 0:
        #     ## в текущем пути нет имени страницы это корень сайта. Здесь нам нужно положить в результат полное имя полученной страницы.
        #     result = path
        else : # путь к ресурсу в текущем пути представлен не только ресурсом
            ## нужно объединить path предыдущей страницы и текущий, извлеченный из ссылки
            ## это будет рабоать если только скрапинг в пределах одного сайта.
            # result_as_list = urllib.parse.urlparse(self.currenrt_scraped_page.page_url).path.split('/')[:-1]
            # result_as_list.append(path)
            result = (Path(self.currenrt_scraped_page_context) / path).as_posix()
        self.next_page_url = result

    def set_next_page_url_to_currenrt_scraped_page(self):
        self.currenrt_scraped_page.reset_page_url(self.next_page_url)
        self.next_page_url:Page = None
        self.currenrt_scraped_page_context = None
        self.soup = None


def get_next_page_url(content)->str:
    try:
        url = content.find('div', attrs={'class' : 'col-sm-8 col-md-9'}).find('ul', class_='pager').find('li', class_='next').find('a').get('href')
    except:
        url = None
    return url


def find_blocks(content):
    for block in content.find_all('ol', attrs={'class' : 'row'}):
        yield block


def find_item(content):
    for item in content.find_all('article'):
        yield item


class ExtractBlocks:
    def __init__(self, content):
        self.content = content
        self.block_list = []

    def extract(self, foo):
        for block in foo(self.content):
            self.block_list.append(block)


class ExtractItems:
    def __init__(self, content):
        self.content = content
        self.item_list = []

    def extract(self, foo):
        for item in foo(self.content):
            self.item_list.append(item)

def extract_fields_from_items(content)->dict:
    """
    Возвращает словарь с полями из блока контента
    """
    result = {}
    try: 
        result['name'] = content.find('h3').find('a')['title']
    except:
        result['name'] = None
    try:
        result['price'] = content.find('div', class_='product_price').find('p', class_='price_color').text.replace('£','')
    except:
        result['price']
    try:
        result['avaiability'] = 1 if content.find(class_='instock availability').find('i')['class'][0] == 'icon-ok' else 0
    except:
        result['avaiability'] = None
    try:
        result['url'] = content.find('h3').find('a').get('href',None)
    except:
        result['url'] = None
    return result

def extract_quantity(content):
    try:
        content_list = content.find('article', attrs={'class':'product_page'}).find('p', attrs={'class': 'instock availability'}).contents
        quantity_as_str = [el.replace('\n','').strip() for el in content_list if 'available' in el][0]\
            .split('(')[1].split()[0]
        quantity = int(quantity_as_str)
    except:
        quantity = None
    return quantity


def main():
    site = Site(BASE_URL)
    params = RequestParams(HEADERS)
    page = Page(site, PAGE_URL_START, params)
    scraper = Scraper(page)
    items_as_dict = []
    page_process_num = 0
    while True:
        logging.info(f'Обработка страницы: {scraper.currenrt_scraped_page.page_url}')
        scraper.load_content_and_parse(parser = 'html.parser')
        if scraper.currenrt_scraped_page.page_load_status != PAGE_LOAD_STATUS_OK:
            logging.info(f'Ошибка загрузки страницы. http код: {scraper.currenrt_scraped_page.responce_last_status_code} url : {scraper.currenrt_scraped_page.page_url} ')            
            break
        blocks = ExtractBlocks(scraper.soup)
        blocks.extract(find_blocks)
        for block in blocks.block_list:
            items = ExtractItems(block)
            items.extract(find_item)
            for item in items.item_list:
                item_as_dict = extract_fields_from_items(item)                
                if item_as_dict['name']:
                    try:
                        item_as_dict['price'] = item_as_dict['price']
                    except:
                        item_as_dict['price'] = None
                    item_as_dict['context'] = scraper.currenrt_scraped_page_context
                    items_as_dict.append(item_as_dict)
        page_process_num += 1
        if PAGE_PROCESS_NUM_MAX > 0 and page_process_num >= PAGE_PROCESS_NUM_MAX:
            break
        scraper.extract_and_set_next_page_url(get_next_page_url)        
        if scraper.next_page_url:
            scraper.set_next_page_url_to_currenrt_scraped_page()
            time.sleep(TIMEOUT_MILLISEC / 10**3)
        else:
            break    
    logging.info(f'Обработано страниц {page_process_num}.')
    if EXTRACT_QUANTITY:
        logging.info(f'Извлекаем количество.')
        for item in items_as_dict:
            if item['avaiability'] == 1:
                scraper.set_next_page_url(item['url'], context=item['context'])
                scraper.set_next_page_url_to_currenrt_scraped_page()
                scraper.load_content_and_parse(parser = 'html.parser')
                if scraper.currenrt_scraped_page.page_load_status != PAGE_LOAD_STATUS_OK:
                    print(f'Ошибка загрузки страницы. http код: {scraper.currenrt_scraped_page.responce_last_status_code} url : {scraper.currenrt_scraped_page.page_url} ')            
                    continue
                quantity = extract_quantity(scraper.soup)
                if quantity:
                    item['quantity'] = quantity
        logging.info(f'Сохранение информации. Количество объектов : {len(items_as_dict)}.')
    for item_as_dict in items_as_dict:
        item_as_dict['url'] = (Path(item_as_dict['context']) / item_as_dict['url']).as_posix()
        del item_as_dict['context']
    result_abs_file_name = Path(__file__).parent / RESULT_FILE_NAME
    with open(result_abs_file_name, 'w') as f:
        json.dump(items_as_dict,f )
    logging.info(f'Данные сохранены в файл : {result_abs_file_name}.')

if __name__ == '__main__':
    main()
