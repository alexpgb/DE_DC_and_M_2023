# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy



class UnsplashComItem(scrapy.Item):
    """
    3. Определите элемент (Item) в Scrapy, который будет представлять изображение. 
    Ваш элемент должен включать такие детали, как
 -  URL изображения,
 -  название изображения
 -  и категорию, к которой оно принадлежит.
    """
    description = scrapy.Field()
    image_urls = scrapy.Field()
    category = scrapy.Field()
    author = scrapy.Field()
    file_name = scrapy.Field()
    
