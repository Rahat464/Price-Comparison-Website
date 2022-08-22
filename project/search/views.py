import json  # Parse API Request
import mysql.connector  # Connect to MySQL local database server
import requests  # Make API Requests
import scrapy  # Scrape websites
import time  # for time.sleep
import plotly.graph_objects as go  # Plot data for price history graphs
from crochet import setup  # Fix ReactorAlreadyRunning error
from scrapy.crawler import CrawlerRunner  # To run mulitple scrapy spiders at the same time
from django.db.models import Q  # Make queries
from django.shortcuts import render  # Render HTML page requests
from .models import amazon, ebay, newegg  # Obtain data on models
from datetime import datetime  # Read and write in datetime format

setup()  # Crochet startup

# Establish connection with local MySQL server
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="root",  # Database password has been omitted for security reasons
    database="database",
)
mycursor = db.cursor()  # Make DB execution code cleaner
db.autocommit = True  # Minimise time taken for Django to select newly inserted data


# GET scrapy scraping settings
def scrapy_settings():
    settings = dict()
    settings["ROBOTSTXT_OBEY"] = False


class NeweggSpider(scrapy.Spider):
    name = 'newegg'

    # Initiate instance to allow arguments to pass through scrapy spider
    def __init__(self, keyword="", **kwargs):
        self.allowed_domains = ['newegg.com/global/uk-en/']
        self.start_urls = ["https://www.newegg.com/global/uk-en/p/pl?d={}".replace("{}", keyword)]
        super().__init__(**kwargs)

    def parse(self, response, **kwargs):
        items = {
            "newegg_product_name": None,
            "newegg_product_price": None,
            "newegg_product_imagelink": None,
            "newegg_product_productlink": None,
        }

        #  Define XPATH/CSS selectors to fetch correct data
        newegg_product_name = (response.css(".item-cell .item-title::text").extract())
        newegg_product_price = response.css(".item-cell strong::text").extract()
        newegg_product_price = [x for x in newegg_product_price if x.isdigit()]
        newegg_product_imagelink = (response.css(".item-cell .item-img img").xpath("@src").extract())[:512]
        newegg_product_productlink = response.css(".item-cell .item-title").xpath("@href").extract()[:700]

        # Declare values to items dictionary
        items["newegg_product_name"] = newegg_product_name
        items["newegg_product_price"] = newegg_product_price
        items["newegg_product_imagelink"] = newegg_product_imagelink
        items["newegg_product_productlink"] = newegg_product_productlink

        # Find length of shortest list in items dictionary to prevent IndexError when iterating through the product data
        lengths = [len(items["newegg_product_productlink"]), len(items["newegg_product_name"]),
                   len(items["newegg_product_price"]), len(items["newegg_product_imagelink"])]
        list_index = min(lengths)

        # Iterate through list and commit data to local MySQL server
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

        yield items


class EbaySpider(scrapy.Spider):
    name = 'ebay'

    # Initiate instance to allow arguments to pass through scrapy spider
    def __init__(self, keyword="", **kwargs):
        self.allowed_domains = ['ebay.co.uk/']
        self.start_urls = ["https://www.ebay.co.uk/sch/i.html?_nkw={}&_oaa=1&_dcat=11071&LH_ItemCondition=1000&LH_Pre"
                           "fLoc=1&_sop=12".replace("{}", keyword)]
        super().__init__(**kwargs)

    def parse(self, response, **kwargs):
        items = {
            "ebay_product_name": None,
            "ebay_product_price": None,
            "ebay_product_imagelink": None,
            "ebay_product_productlink": None,
        }

        # Define XPATH/CSS selectors to fetch correct data
        ebay_product_name = response.xpath("//h3[@class='s-item__title']/text()").extract()
        ebay_product_price = response.xpath("//span[@class='s-item__price']/text()").extract()
        ebay_product_imagelink = response.css("img.s-item__image-img").xpath("@src").extract()
        ebay_product_productlink = response.css("a.s-item__link").xpath("@href").extract()
        del ebay_product_productlink[0]

        # Declare values to items dictionary
        items["ebay_product_name"] = ebay_product_name
        items["ebay_product_price"] = ebay_product_price
        items["ebay_product_imagelink"] = ebay_product_imagelink
        items["ebay_product_productlink"] = ebay_product_productlink

        # Find length of shortest list in items dictionary to prevent IndexError when iterating through the product data
        lengths = [len(items["ebay_product_productlink"]), len(items["ebay_product_name"]),
                   len(items["ebay_product_price"]), len(items["ebay_product_imagelink"])]
        list_index = min(lengths)

        # Iterate through list and commit data to local MySQL server
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
        print("Ebay Commited!")
        yield items


def amazon_api(keyword):
    # Sample code from RapidAPI
    url = "https://amazon-price1.p.rapidapi.com/search"
    querystring = {"marketplace": "GB", "keywords": keyword}
    headers = {
        'x-rapidapi-key': "6b08698a4fmsh8063f024dff7edcp117fe7jsn0f24382fb22f",  # API KEY removed for precautions
        'x-rapidapi-host': "amazon-price1.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    data = json.loads(response.text)  # Parse JSON data into python-readable data

    for i in range(10):
        mycursor.execute(
            "INSERT INTO search_amazon (ASIN, name, price, image_link, product_link, rating, datetime)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (data[i]["ASIN"],
             data[i]["title"],
             data[i]["price"],
             data[i]["imageUrl"],
             data[i]["detailPageURL"],
             data[i]["rating"],
             datetime.now())
        )
    db.commit()
    print("Amazon Commited!")


# Incomplete code.
def graph(products):
    """
    for item in products:
    """

    Price = [330.26, 340.95, 199.99]
    Date = ["2022-01-07 06:35:00.000000", "2022-01-09 15:21:00.000000", "2022-01-18 04:12:00.000000"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=Date, y=Price, line_shape='vh'))
    fig.update_layout(
        title='WD_BLACK D30 2TB Game Drive SSD - speed and storage, compatible with Xbox Series X|S and PlayStation 5',
        xaxis_title='Date', yaxis_title='Price')
    
    # fig.show()
    graph_html = plotly.offline.plot(fig, auto_open=False, output_type="div")
    return graph_html


# Determine what to output depending on which filter/sort settings the user selected
def query(request, keyword):
    keyword = request.GET.get('q').replace(" ", "+")
    products = []

    # if amazon is on
    if request.GET.get('amazoncheck') == "on":
        products = []
        # If both/neither asc and desc are checked
        if request.GET.get('asc') == "on" and request.GET.get('desc') == "on" or \
                request.GET.get('asc') is None and request.GET.get('desc') is None:
            products = amazon.objects.filter(name__icontains=request.GET.get('q'))

        # If asc is on
        if request.GET.get('asc') == "on":
            products = amazon.objects.filter(name__icontains=request.GET.get('q')).order_by('price')
            return products

        # If desc is on
        if request.GET.get('desc') == "on":
            products = amazon.objects.filter(name__icontains=request.GET.get('q')).order_by('-price')
            return products

    # if newegg is on
    if request.GET.get('neweggcheck') == "on":
        products = []
        # If both/neither asc and desc are checked
        if request.GET.get('asc') == "on" and request.GET.get('desc') == "on" or \
                request.GET.get('asc') is None and request.GET.get('desc') is None:
            products = newegg.objects.filter(name__icontains=request.GET.get('q'))

        # If asc is on
        if request.GET.get('asc') == "on":
            products = newegg.objects.filter(name__icontains=request.GET.get('q')).order_by('price')
            return products

        # If desc is on
        if request.GET.get('desc') == "on":
            products = newegg.objects.filter(name__icontains=request.GET.get('q')).order_by('-price')
            return products

    # if ebay is on
    if request.GET.get('ebaycheck') == "on":
        products = []
        # If both/neither asc and desc are checked
        if request.GET.get('asc') == "on" and request.GET.get('desc') == "on" or \
                request.GET.get('asc') is None and request.GET.get('desc') is None:
            products = ebay.objects.filter(name__icontains=request.GET.get('q'))

        # If asc is on
        if request.GET.get('asc') == "on":
            products = ebay.objects.filter(name__icontains=request.GET.get('q')).order_by('price')
            return products

        # If desc is on
        if request.GET.get('desc') == "on":
            products = ebay.objects.filter(name__icontains=request.GET.get('q')).order_by('-price')
            return products

    # If amazon and newegg are on
    if request.GET.get('amazoncheck') and request.GET.get('neweggcheck') == "on":
        products = []
        # If both/neither asc and desc are checked
        if request.GET.get('asc') and request.GET.get('desc') == "on" or \
                request.GET.get('asc') and request.GET.get('desc') is None:

            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, newegg):
                products.extend(model.objects.filter(search_query))
            return products

        # If asc is on
        if request.GET.get('asc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, newegg):
                products.extend(model.objects.filter(search_query).order_by('price'))
            return products

        # If desc is on
        if request.GET.get('desc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, newegg):
                products.extend(model.objects.filter(search_query).order_by('-price'))
            return products

    # if amazon and ebay are on
    if request.GET.get('amazoncheck') and request.GET.get('ebaycheck') == "on":
        products = []
        # If both/neither asc and desc are checked
        if request.GET.get('asc') and request.GET.get('desc') == "on" or \
                request.GET.get('asc') and request.GET.get('desc') is None:

            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, ebay):
                products.extend(model.objects.filter(search_query))
            return products

        # If asc is on
        if request.GET.get('asc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, ebay):
                products.extend(model.objects.filter(search_query).order_by('price'))
            return products

        # If desc is on
        if request.GET.get('desc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, ebay):
                products.extend(model.objects.filter(search_query).order_by('-price'))
            return products

    # if newegg and ebay are on
    if request.GET.get('neweggcheck') == "on" and request.GET.get('ebaycheck') == "on":
        products = []
        # If both/neither asc and desc are checked
        if request.GET.get('asc') == "on" and request.GET.get('desc') == "on" or \
                request.GET.get('asc') is None and request.GET.get('desc') is None:

            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, newegg, ebay):
                products.extend(model.objects.filter(search_query))
            return products

        # If asc is on
        if request.GET.get('asc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (newegg, ebay):
                products.extend(model.objects.filter(search_query).order_by('price'))
            return products

        # If desc is on
        if request.GET.get('desc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (newegg, ebay):
                products.extend(model.objects.filter(search_query).order_by('-price'))
            return products

    # If all 3 amazon, newegg and ebay are checked OR none are checked.
    if request.GET.get('amazoncheck') and request.GET.get('neweggcheck') and request.GET.get('ebaycheck') == "on" or \
            request.GET.get('amazoncheck') is None and request.GET.get('neweggcheck') is None and \
            request.GET.get('ebaycheck') is None:
        products = []

        # If both/neither asc and desc are checked
        if request.GET.get('asc') == "on" and request.GET.get('desc') == "on" or \
                request.GET.get('asc') is None and request.GET.get('desc') is None:

            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, newegg, ebay):
                products.extend(model.objects.filter(search_query))

            return products

        # If asc is on
        if request.GET.get('asc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, newegg, ebay):
                products.extend(model.objects.filter(search_query).order_by('price'))
            return products

        # If desc is on
        if request.GET.get('desc') == "on":
            search_query = Q(name__icontains=request.GET.get('q'))
            for model in (amazon, newegg, ebay):
                products.extend(model.objects.filter(search_query).order_by('-price'))
            return products

    return products


def search(request):
    keyword = request.GET.get('q')  # Get input from website
    if keyword is not None or keyword != "":  # Validate input
        # Collect data from API and Scrapy
        runner = CrawlerRunner(settings=scrapy_settings())
        runner.crawl(NeweggSpider, keyword=keyword)
        runner.crawl(EbaySpider, keyword=keyword)
        amazon_api(keyword)

        products = query(request, keyword)  # Check which results to return to the user
        time.sleep(1)  # Wait for data to be inserted into MySQL database
        return render(request, 'search/search.html', {"products": products})

    # If input is not valid, do not allow search to go through and waste system resources
    products = None
    return render(request, 'home_page/home_page.html', {"products": products})
