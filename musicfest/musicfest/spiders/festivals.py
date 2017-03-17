import scrapy


class FestivalSpider(scrapy.Spider):
    name = 'festival'

    custom_settings = {
        #"DOWNLOAD_DELAY": 1,
        #"CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "HTTPCACHE_ENABLED": True
    }

    def start_requests(self):
        start_url = 'https://www.musicfestivalwizard.com/festival-guide/us-festivals/'
        yield scrapy.Request(url=start_url, callback=self.get_fests)

    def get_fests(self, response):
        for i in response.xpath('//div[@class="h-event"]'):
            url = i.xpath('./h2/span[2]/span[2]/a/@href').extract()[0]
            yield scrapy.Request(url=url, callback=self.parse, meta={'url':url})
        try:
            next_url = response.xpath('//div[@class="pagination"]/ul/li/a[@class="next page-numbers"]/@href').extract()[0]
            if next_url == "https://www.musicfestivalwizard.com/festival-guide/us-festivals/page/10/":
                next_url = "https://www.musicfestivalwizard.com/festival-guide/us-festivals/page/11/"
            yield scrapy.Request(url=next_url, callback=self.get_fests)
        except:
            page10 = [
                "https://www.musicfestivalwizard.com/festivals/bonanza-campout-2017/",
                "https://www.musicfestivalwizard.com/festivals/madsummer-meltdown-2017/",
                "https://www.musicfestivalwizard.com/festivals/frendly-gathering-2017/",
                "https://www.musicfestivalwizard.com/festivals/electric-forest-2017/",
                "https://www.musicfestivalwizard.com/festivals/high-sierra-music-festival-2017/",
                "https://www.musicfestivalwizard.com/festivals/essence-music-festival-2017/",
                "https://www.musicfestivalwizard.com/festivals/moe-down-2017/",
                "https://www.musicfestivalwizard.com/festivals/highberry-2017/",
                "https://www.musicfestivalwizard.com/festivals/8035-music-festival-2017/",
                "https://www.musicfestivalwizard.com/festivals/summerfest-2017/",
                "https://www.musicfestivalwizard.com/festivals/the-ride-festival-2017/",
                "https://www.musicfestivalwizard.com/festivals/levitate-festival-2017/"
            ]
            for url in page10:
                yield scrapy.Request(url=url, callback=self.parse, meta={'url':url})
            next

    def parse(self, response):
        try:
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
            lineup = response.xpath('//div[@class="lineupguide"]/ul/li/text()').extract()
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
        except:
            next
