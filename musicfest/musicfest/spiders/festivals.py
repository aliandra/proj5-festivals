import scrapy
import logging


class FestivalSpider(scrapy.Spider):
    name = 'festival'

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "HTTPCACHE_ENABLED": True
    }

    start_urls = [
        'https://www.musicfestivalwizard.com/festival-guide/us-festivals/',
        'https://www.musicfestivalwizard.com/festival-guide/canada-festivals/'
    ]


    def parse(self, response):
        # follow links to festival pages
        logging.warning('about to start')
        for href in response.xpath('//span[@class="festivaltitle"]/a/@href').extract():
            logging.warning('about to follow url')
            yield scrapy.Request(url=href, callback=self.parse_festival, meta={'url':href})

        # follow pagination links
        try:
            next_url = response.xpath('//div[@class="pagination"]/ul/li/a[@class="next page-numbers"]/@href').extract()[0]
            yield scrapy.Request(url=next_url, callback=self.parse)
        except IndexError:
            next


    def parse_festival(self, response):
        logging.warning('about to parse')
        url = response.request.meta['url']
        name = response.xpath('//header/h1/span/text()').extract()[0]
        location = response.xpath('//div[@id="festival-basics"]/text()').extract()[3]
        dates = response.xpath('//div[@id="festival-basics"]/text()').extract()[5]
        tickets = response.xpath('//div[@id="festival-basics"]/text()').extract()[7]
        camping = response.xpath('//div[@id="festival-basics"]/text()').extract()[9]
        website = response.xpath('//div[@id="festival-basics"]/a/@href').extract()[0]
        description = response.xpath('//div[@id="festival-basics"]/text()').extract()[12]
        if not description:
            description = response.xpath('//div[@id="festival-basics"]/text()').extract()[13]
        image = response.xpath('//div[@id="festival-basics"]/img/@src').extract()[0]
        lineup = response.xpath('//div[@class="lineupguide"]/ul/li/text()').extract() + response.xpath('//div[@class="lineupguide"]/ul/li/a/text()').extract()
        poster = response.xpath('//div[@id="festival-poster"]/img/@src').extract()
        
        yield {
            'url': url,
            'name': name,
            'location': location,
            'dates': dates,
            'tickets': tickets,
            'camping': camping,
            'website': website,
            'description': description,
            'image': image,
            'lineup': lineup,
            'poster': poster
        }
