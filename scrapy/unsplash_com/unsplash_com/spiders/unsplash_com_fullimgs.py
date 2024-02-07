import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import HtmlResponse # это мы делаем, чтобы линтер посвечивал атрибуты и методы класса
from scrapy.loader import ItemLoader
from ..items import UnsplashComItem
from itemloaders.processors import MapCompose
from scrapy.pipelines.images import ImagesPipeline
from pathlib import Path


class UnsplashComFullimgsSpider(CrawlSpider):
    name = "unsplash_com_fullimgs"
    allowed_domains = ["unsplash.com", "images.unsplash.com"]
    start_urls = ["https://unsplash.com/"]    

    # rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse_item", follow=True),)
    # Для разнообразия сделаем, как на лекции
    rules = (
        # Правило, выделяющее ссылки на категории изображений на стартовой странице.    
        Rule(LinkExtractor(restrict_xpaths="//ul/li/a[contains(@class, 'p7ajO') and contains(@href, '/t/')]")),
        # Правило, выделяющее ссылки на страницы с изображениями на странице с категориями изображений
        Rule(LinkExtractor(restrict_xpaths="//figure[@itemprop='image' and @itemscope]//a[@itemprop='contentUrl' and @title]/parent::figure/a"), callback="parse_item", follow=True),
        )
    # rules = (Rule(LinkExtractor(restrict_xpaths="//ul/li/a"), callback="parse_item", follow=True),)

    def parse_item(self, response:HtmlResponse):
        # print(f'{response.url=}')
        loader = ItemLoader(item=UnsplashComItem(), response=response)
        loader.default_input_processor = MapCompose(str.strip)
        loader.add_xpath("description", "//div/div/h1/text()")
        loader.add_xpath("category", "//div/h3/parent::div[1]/span//a/text()")
        loader.add_xpath("author", "//div[@class='TO_TN']/a/text()")
        # print(f'''image_urls: {response.xpath("//div/div/a[@title]/span[text()='Download free']/parent::a[1]/@href").getall()}''')
        # loader.add_value("image_urls", response.xpath("//div/div/a[@title]/span[text()='Download free']/parent::a[1]/@href").getall())
        # loader.add_value("image_urls", response.xpath("//button/div/div/img/@src").getall())
        image_urls = response.xpath("//div/div/a[@title]/span[text()='Download free']/parent::a[1]/@href").getall()
        print(f"{image_urls=}")
        loader.add_value("image_urls", image_urls)
        # if image_url:
        #     yield response.follow(url=image_url, callback=self.save__image)
        yield loader.load_item()
