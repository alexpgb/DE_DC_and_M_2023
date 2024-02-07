import scrapy
from scrapy.http import HtmlResponse # это мы делаем, чтобы линтер посвечивал атрибуты и методы класса

class ContentSpiderSpider(scrapy.Spider):
    name = "content_spider"
    allowed_domains = ["n-katalog.ru"]
    start_urls = ["https://n-katalog.ru/category/plity/list"]
    # start_urls = ["https://n-katalog.ru/category/plity/list/page-47"]

    def parse(self, response: HtmlResponse):
        # Если мы хотим получить результат обработки в виде строки вызываем для метода xpath() метод get() или getall()
        # Если хотим вернуть объекты для последующей обработки методом  xpath() или другим, то после xpath() ничего не пишем.
        next_page_url = \
            response.xpath("//div[@class='list-pager-div']/div[@class='list-pager']/div[contains(@class, 'page-num')]/a[contains(@class, 'select')]/following-sibling::a[1]/@href").get()
        # ожидаем объект вида ['/category/mobilnye-telefony/list/page-2']
        # Если такого элемента нет возвращается None
        # сначала нужно вызвать метод обхода страниц, потом продолжить парсить страницу 
        # в т.ч. выполнить переход на страницу, содержащую детальные данные
        if next_page_url:
            yield response.follow(url=next_page_url, callback=self.parse)
            # т.к. страницы однотипные, для парсинга вызываем самого себя
        # найдем все вхождения блоков с интересующей нас информацией на странице
        content_blocks = response.xpath("//div[contains(@class, 'model-short-div')]")
        item_short_criteria_list = [
            {'field_name': 'name',
            'locator': ".//td[@class='model-short-info']/table//a/span/text()"},
            {'field_name': 'detail_page_url',
            'locator': ".//td[@class='model-short-info']/table//a/@href"},
        ]
        # print(f'{len(content_blocks)=}')
        for blocks in content_blocks:
            item_short = {}
            for field in item_short_criteria_list:
                value = blocks.xpath(field['locator']).get()
                if value is not None:
                    item_short[field['field_name']] = value
            # print(f"{item_short=}")
            yield response.follow(url=item_short['detail_page_url'], callback=self.parse_detail_item, meta={'item_name': item_short['name']})
            # break

    def parse_detail_item(self, response: HtmlResponse):
        # print(f"{response.request.meta}")
        name = response.request.meta['item_name']
        item_detail_blocks = response.xpath("//div[@id='mainBlockItem']//table[@id='help_table']")
        item_detail_criteria_list = [
            {'field_name': 'cooking_surface',
            'locator': ".//span[contains(text(), 'Тип варочной поверхности')]/../following-sibling::td/text()",
            'postprocess': lambda x : x.replace("\n", "").strip()},
            {'field_name': 'number of burners',
            'locator': ".//span[contains(text(), 'Кол-во газовых конфорок')]/../following-sibling::td/text()",
            'postprocess': lambda x : x.replace("\n", "").strip()},
            {'field_name': 'oven_type',
            'locator': ".//span[contains(text(), 'Тип духовки')]/../following-sibling::td/text()",
            'postprocess': lambda x : x.replace("\n", "").strip()},
            {'field_name': 'burners_grill_type',
            'locator': ".//span[contains(text(), 'Решетки конфорок')]/../following-sibling::td/text()",
            'postprocess': lambda x : x.replace("\n", "").strip()},
            {'field_name': 'functions',
            'locator': ".//span[contains(text(), 'Функции')]/../following-sibling::td/text()",
            'postprocess': lambda x : x.replace("\n", "").strip()},
        ]
        item_detail = {
            'name' : name
        }
        for field in item_detail_criteria_list:
            value = item_detail_blocks[0].xpath(field['locator']).get()
            if value is not None:
                item_detail[field['field_name']] = value
                if field.get('postprocess') is not None:
                    item_detail[field['field_name']] = field['postprocess'](item_detail[field['field_name']])
        # print(f'{item_detail=}')
        yield item_detail
