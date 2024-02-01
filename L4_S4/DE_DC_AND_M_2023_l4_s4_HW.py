"""
Выберите веб-сайт с табличными данными, который вас интересует.
Напишите код Python, использующий библиотеку requests для отправки HTTP GET-запроса на сайт и получения HTML-содержимого страницы.
Выполните парсинг содержимого HTML с помощью библиотеки lxml, чтобы извлечь данные из таблицы.
Сохраните извлеченные данные в CSV-файл с помощью модуля csv.

Ваш код должен включать следующее:

Строку агента пользователя в заголовке HTTP-запроса, чтобы имитировать веб-браузер и избежать блокировки сервером.
Выражения XPath для выбора элементов данных таблицы и извлечения их содержимого.
Обработка ошибок для случаев, когда данные не имеют ожидаемого формата.
Комментарии для объяснения цели и логики кода.

Воспользуемся наработками ДЗ #2 в части скрапера и поменяем только функции, извлекающие данные со страницы.
"""

import requests
from lxml import html
import csv
import urllib
import time
import logging
from pathlib import Path


BASE_URL = 'https://finance.yahoo.com/'
RESULT_FILE_NAME = 'l4_s4_t1_hw.csv'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
TIMEOUT_MILLISEC = 1000
HEADERS = {}
HEADERS['User-Agent'] = USER_AGENT
PAGE_LOAD_STATUS_OK = 1
PAGE_LOAD_STATUS_NOT_LOADED = 0
PAGE_LOAD_STATUS_ERROR = -1
PAGE_URL_START = 'most-active/' # ''
PAGE_PROCESS_NUM_MAX = -1 # - без ограничения количества обрабатываемых страниц


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
       self.params:RequestParams = params
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
        self.dom = None

    def load_content_and_parse(self, parser):
        self.currenrt_scraped_page.load_page_content()
        if self.currenrt_scraped_page.page_load_status == PAGE_LOAD_STATUS_OK:
            self.currenrt_scraped_page_context = Path(urllib.parse.urlparse(self.currenrt_scraped_page.page_url).path).parent.as_posix()
            self.dom = parser(self.currenrt_scraped_page.page_content)


    def extract_and_set_next_page_url(self, foo):
        path = foo(self.dom)
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
        self.dom = None


def get_next_page_url(content)->str:
    """
    Возвращает True если на странице есть объекты для парсинга, False в противном случае.
    """
    url = None
    urls = content.xpath("//div[@id='scr-res-table']/div/table/tbody/tr")
    if len(urls) == 0:
        url = urls[0]
    return url

def is_content_exists(content)->str:
    """
    Возвращает True если на странице есть объекты для парсинга, False в противном случае.
    """
    result = False
    if len(content.xpath("//div[@id='scr-res-table']/div/table/tbody/tr")) > 0:
        result = True
    return result


def find_blocks(content):
    for block in content.xpath("//div[@id='scr-res-table']/div/table/tbody"):
        yield block


def find_item(content):
    for item in content.xpath('./tr'):
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
    Возвращает словарь с полями из части контента
    """
    result = {}
    try: 
        result['symbol'] = content.xpath("./td/a/text()")[0] # PLUG
    except:
        result['symbol'] = None
    try:
        result['price'] = content.xpath("./td/node()[@data-field='regularMarketPrice']/text()")[0] # 4.6298
    except:
        result['price']
    try:
        result['change_abs'] = content.xpath("./td/node()[@data-field='regularMarketChange']/span/text()")[0] # +0.8998
    except:
        result['change_abs'] = None
    try:
        result['change_rel_percent'] = content.xpath("./td/node()[@data-field='regularMarketChangePercent']/span/text()")[0].replace('%','') # +24.12%
    except:
        result['change_rel_percent'] = None
    try:
        result['volume'] = content.xpath("./td/node()[@data-field='regularMarketVolume']/text()")[0].replace('M','') # 99.554M
    except:
        result['volume'] = None
    try:
        result['avg_vol_three_month'] = content.xpath("./td[@aria-label='Avg Vol (3 month)']/text()")[0].replace('M','') # 69.141M
    except:
        result['avg_vol_three_month'] = None
    try:
        result['market_cap'] = content.xpath("./td/node()[@data-field='marketCap']/text()")[0] # 273.343B
    except:
        result['market_cap'] = None
    try:
        result['pe_ratio_ttm'] = content.xpath("./td[@aria-label='PE Ratio (TTM)']/text()")[0].replace(',','') # 1,692.00
    except:
        result['pe_ratio_ttm'] = None
    return result


def process_item(item:dict)->bool:
    result = False
    if item['symbol']:
        result = True
        try:
            item['price'] = float(item['price'])
        except:
            item['price'] = None
        try:
            item['change_abs'] = float(item['change_abs'])
        except:
            item['change_abs'] = None
    return result


def main():
    offset = 0
    limit = 25
    params_in_query = {
        'offset': offset,
        'size': limit
    }
    site = Site(BASE_URL)
    params = RequestParams(HEADERS, params_in_query)
    page = Page(site, PAGE_URL_START, params)
    scraper = Scraper(page)
    items_as_dict = []
    page_process_num = 0
    while True:
        logging.info(f'Обработка страницы: {scraper.currenrt_scraped_page.page_url}, params: {scraper.currenrt_scraped_page.params.params_in_query}')
        scraper.load_content_and_parse(parser = html.fromstring)
        if scraper.currenrt_scraped_page.page_load_status != PAGE_LOAD_STATUS_OK:
            logging.info(f'Ошибка загрузки страницы. http код: {scraper.currenrt_scraped_page.responce_last_status_code} url : {scraper.currenrt_scraped_page.page_url}')            
            break
        blocks = ExtractBlocks(scraper.dom)
        blocks.extract(find_blocks)
        if len(blocks.block_list) == 0 or not is_content_exists(scraper.dom):
            # закончился контент для скрапинга
            break
        for block in blocks.block_list:
            items = ExtractItems(block)
            items.extract(find_item)
            for i, item in enumerate(items.item_list):
                item_as_dict = extract_fields_from_items(item)                
                if process_item(item_as_dict):
                    items_as_dict.append(item_as_dict)
                if page_process_num == 0 and i == 0:
                    keys_as_list = list(item_as_dict.keys())
        page_process_num += 1
        if PAGE_PROCESS_NUM_MAX > 0 and page_process_num >= PAGE_PROCESS_NUM_MAX:
            break
        time.sleep(TIMEOUT_MILLISEC / 10**3)
        params_in_query['offset'] += params_in_query['size']
        scraper.currenrt_scraped_page.params.params_in_query = params_in_query
    logging.info(f'Обработано страниц {page_process_num}.')
    result_abs_file_name = Path(__file__).parent / RESULT_FILE_NAME
    if len(items_as_dict) > 0:
        with open(result_abs_file_name, 'w', encoding='utf-8', newline='') as f:
            csvwriter = csv.DictWriter(f, fieldnames=keys_as_list)
            csvwriter.writeheader()
            for item_as_dict in items_as_dict:
                csvwriter.writerow(item_as_dict)
        logging.info(f'Данные сохранены в файл : {result_abs_file_name}.')
    else:
        logging.info(f'Нет данных для сохранения. Файл не сформирован.')


if __name__ == '__main__':
    main()
