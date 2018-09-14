import scrapy
import datetime
# TODO: rename files
from autoria_crawler.items import AutoriaCrawlerItem

'''
    Scraper for used cars from 'http://autoportal.ua/'

    @author Maxim G.
    @date 13.09.2018
'''

class AutoPortalSpider(scrapy.Spider):
    name = "autoportal"

    start_urls = [
        'http://sale.autoportal.ua/filters.html?vehicle_id=1',  #passenger cars
        'http://sale.autoportal.ua/filters.html?vehicle_id=5'   #minibuses
    ]

    lastUpdate = datetime.datetime(1, 1, 1)
    currencyQuantity = '$'
    mileageQuantity = 'км'

    def parse(self, response):
        def prepare_href(advr):
            updateDate = AutoPortalSpider.txt2date(advr.css('p.br05::text').extract_first())
            
            href = advr.css('a.vrtcl_itm::attr(href)').extract_first()
            if (href and updateDate > self.lastUpdate):
                return response.follow(href, self.parse_advr)
             
        for advr in response.css('div.ads_fltr-hot'):
            yield prepare_href(advr)
        for advr in response.css('div.ads_fltr'):
            yield prepare_href(advr)
    
        for next_page in response.css('a.pnext'):
            yield response.follow(next_page, callback=self.parse)

        #with open('autoportal.json', 'wb') as f:
        #    f.write(response.body)

    def parse_advr(self, response):
        url = response.request.url

        block_data = response.xpath('//div[@class="ad_bit2 cell6"]')
        updateTime = AutoPortalSpider.txt2date(block_data.css('ad_bit2_height i::text').extract_first())
        li_rows = block_data.css('ul.twoCol_dot li')
        
        fullname = li_rows[0].css('span::attr(title)').extract_first()
        
        brand = AutoPortalSpider.getBrand(response)
        model = AutoPortalSpider.getModel(fullname, brand)
        
        def getliText(index):
            return li_rows[index].css('b::text').extract_first() 

        price = getliText(0).rstrip(self.currencyQuantity).strip()
        year = getliText(1)
        mileage = getliText(2).rstrip(self.mileageQuantity).strip()
        engine_capacity = getliText(3)
        fuel = getliText(4)#AutoPortalSpider.txt2fuel(getliText(4))
        #carcase -- 5
        transmission = getliText(6)#AutoPortalSpider.txt2transmission(getliText(6))
        drive = AutoPortalSpider.txt2drive(getliText(7))
        #color -- 8
        
        photos = response.css('div.preview img::attr(src)').extract()
        # TODO: remove name of classes
        additionalInfo = block_data.css('div.brd_fff').extract()#xpath('//div[@class="factor bg_f1"]').extract_first() #NoSQL

        item = AutoPortalCrawlerItem()
        item['mark_name'] = brand
        item['model_name'] = model
        item['year'] = year
        item['info'] = additionalInfo
        item['url'] = url
        item['price'] = price
        item['mileage'] = mileage
        item['location'] = ""
        # TODO: back to the indexes
        item['fuel'] = fuel
        item['transmission'] = transmission
        item['image'] = photos[0]
        
        if item is not None:
            yield item

        '''
        yield {
            "url": url,
            "updateTime": updateTime,

            "state": 0, # 0 - used, 1 - new     Is it really need?
            "name" : {
                "full": fullname, 
                "brand": brand, 
                "model": model
            },
            "year": year,
            "mileage": {
                "quantity": self.mileageQuantity,
                "value": mileage
            },
            "price": { 
                "quantity": self.currencyQuantity,
                "value": price
            },

            "fuel": fuel,
            "transmission": transmission,
            "drive": drive, # 0 - undefined, 1 - four-wheel, 2 - rear, 3 - front-wheel
            "engine_capacity": engine_capacity,

            "photos": photos,
            "additional": additionalInfo
        }
        '''

    # TODO: finish
    @staticmethod
    def txt2date(txt):
        return datetime.datetime.now()

    @staticmethod
    def getBrand(response):
        # Get penult bread from breadcrumbs
        breadLine = response.xpath('//div[@id="breadcrumbs"]/div/a/span/text()').extract()[-2]
        # Split first unless word ['Продажа', 'Микроавтобусы']
        txt = breadLine.split(' ', 1)
        # Remaining would be brand of car
        return txt[1]

    @staticmethod
    def getModel(fullname, brand):
        # Only cut brand from fullname and add deffault value for safety
        array = fullname.split(brand, 1)
        if (len(array) > 1):
            return array[1].strip()
        else:
            pass

    @staticmethod
    def txt2fuel(key):
        fuelDict = {
            'Бензин': 0,
            'Дизельное топливо': 1,
            'Газ/бензин': 2,
            'Гибрид': 3
        }
        return fuelDict.get(key, 0)

    @staticmethod
    def txt2transmission(key):
        transDict = {
            'Механика': 0,
            'Роботизированная механика': 1,
            'Автомат': 2,
            'Вариатор': 3
        }
        return transDict.get(key, 0)

    @staticmethod
    def txt2drive(key):
        driveDict = {
            'Полный': 1,
            'Задний': 2,
            'Передний': 3
        }
        return driveDict.get(key, 0) 