import requests
# import re
import json
import scrapy
import mysql.connector
from scrapy.crawler import CrawlerProcess
from datetime import datetime


def scrapy_settings():
    settings = dict()
    settings["ROBOTSTXT_OBEY"] = False
    settings['ITEM_PIPELINES'] = {
        '__main__.EbayPipeline': 1,
        '__main__.NeweggPipeline': 2}


class EbayItem(scrapy.Item):
    ebay_product_name = scrapy.Field()
    ebay_product_price = scrapy.Field()
    ebay_product_imagelink = scrapy.Field()


class NeweggItem(scrapy.Item):
    Newegg_product_name = scrapy.Field()
    Newegg_product_price = scrapy.Field()
    Newegg_product_imagelink = scrapy.Field()
    Newegg_product_productlink = scrapy.Field()


class EbayPipeline(object):
    def process_item(self, items, spider):
        self.store_db(items)
        return items

    def store_db(self, items):
        print("ebay pipeline")
        print(ebayspider)
        lengths = [len(items["ebay_product_productlink"]), len(items["ebay_product_name"]),
                   len(items["ebay_product_price"]), len(items["ebay_product_imagelink"])]
        list_index = min(lengths)

        for i in range(list_index):
            mycursor.execute(
                "INSERT INTO search_ebay (product_link, name, price,"
                "image_link, datetime)"
                "VALUES (%s, %s, %s, %s, %s)",
                (str(items["ebay_product_productlink"][i][:700]),
                 str(items["ebay_product_name"][i][:80]),
                 str(items["ebay_product_price"][i]),
                 str(items["ebay_product_imagelink"][i][:512]),
                 datetime.now())
            )
        db.commit()


class NeweggPipeline(object):
    def process_item(self, items, spider):
        self.store_db(items)
        return items

    def store_db(self, items):
        lengths = [len(items["newegg_product_productlink"]), len(items["newegg_product_name"]),
                   len(items["newegg_product_price"]), len(items["newegg_product_imagelink"])]
        list_index = min(lengths)

        for i in range(list_index):
            mycursor.execute(
                "INSERT INTO search_newegg (product_link, name, price,"
                "image_link, datetime)"
                "VALUES (%s, %s, %s, %s, %s)",
                (str(items["newegg_product_productlink"][i][:512]),
                 str(items["newegg_product_name"][i][:512]),
                 str(items["newegg_product_price"][i]),
                 str(items["newegg_product_imagelink"][i][:512]),
                 datetime.now())
            )
        db.commit()


class EbaySpider(scrapy.Spider):
    name = 'ebay'

    def __init__(self, keyword="", **kwargs):
        self.allowed_domains = ['ebay.co.uk/']
        self.ebay_link = \
            "https://www.ebay.co.uk/sch/i.html?_nkw={}&_oaa=1&_dcat=11071&LH_ItemCondition=1000&LH_PrefLoc=1&_sop=12"
        self.start_urls = [self.ebay_link.replace("{}", keyword)]
        self.custom_settings = {'ITEM_PIPELINES': {'__main__.EbayPipeline': 1}}

        super().__init__(**kwargs)
        # ebay_spider = kwargs.get('keyword')

    def parse(self, response):
        print("ebayspider views.py")
        items = EbayItem()
        items = {
            "ebay_product_name": None,
            "ebay_product_price": None,
            "ebay_product_imagelink": None,
            "ebay_product_productlink": None,
        }

        ebay_product_name = response.xpath("//h3[@class='s-item__title']/text()").extract()
        ebay_product_price = response.xpath("//span[@class='s-item__price']/text()").extract()
        ebay_product_imagelink = response.css("img.s-item__image-img").xpath("@src").extract()
        ebay_product_productlink = response.css("a.s-item__link").xpath("@href").extract()
        del ebay_product_productlink[0]

        items["ebay_product_name"] = ebay_product_name
        items["ebay_product_price"] = ebay_product_price
        items["ebay_product_imagelink"] = ebay_product_imagelink
        items["ebay_product_productlink"] = ebay_product_productlink
        astore_db(items)

        yield items


class NeweggSpider(scrapy.Spider):
    name = 'newegg'

    def __init__(self, keyword="", **kwargs):
        self.allowed_domains = ['newegg.com/global/uk-en/']
        self.start_urls = ["https://www.newegg.com/global/uk-en/p/pl?d={}".replace("{}", keyword)]
        self.custom_settings = {'ITEM_PIPELINES': {'__main__.NeweggPipeline': 2}}

        super().__init__(**kwargs)

    def parse(self, response, **kwargs):
        items = NeweggItem()
        items = {
            "newegg_product_name": None,
            "newegg_product_price": None,
            "newegg_product_imagelink": None,
            "newegg_product_productlink": None,
        }

        newegg_product_name = (response.css(".item-cell .item-title::text").extract())
        newegg_product_price = response.css(".item-cell strong::text").extract()
        newegg_product_price = [x for x in newegg_product_price if x.isdigit()]
        newegg_product_imagelink = (response.css(".item-cell .item-img img").xpath("@src").extract())[:512]
        newegg_product_productlink = response.css(".item-cell .item-title").xpath("@href").extract()[:700]

        items["newegg_product_name"] = newegg_product_name
        items["newegg_product_price"] = newegg_product_price
        items["newegg_product_imagelink"] = newegg_product_imagelink
        items["newegg_product_productlink"] = newegg_product_productlink

        yield items
