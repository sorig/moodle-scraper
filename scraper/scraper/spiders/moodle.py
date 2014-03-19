from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
from scrapy import log
import getpass
import sys

class MoodleSpider(Spider):
    name = "moodle"
    allowed_domains = ["moodle.ucl.ac.uk"]
    start_urls = [
        "https://moodle.ucl.ac.uk/login/index.php"
    ]

    def parse(self, response):
        print "Please input your login credentials."
        sys.stdout.write('Username: ')
        user = raw_input()
        password = getpass.getpass()
        return [FormRequest.from_response(response,
                    formdata={'username': user, 'password': password},
                    callback=self.after_login)]

    def after_login(self, response):
        # check login succeed before going on
        if "loginerrors" in response.body:
            self.log("Login failed", level=log.ERROR)
            return
        # Logged in, crawl moodle home page
        else:
            sel = Selector(response)
            courselinks = sel.xpath('//div[@class="content"]/ul/li/div/a/@href')
            for link in courselinks:
                log.msg("Link: " + str(link.extract()))

    def parse_myhome(self, response):
        """ Scrape useful stuff from page, and spawn new requests

        """
        hxs = HtmlXPathSelector(response)
        images = hxs.select('//img')
        # .. do something with them
        links = hxs.select('//a/@href')
        for link in links:
            log.msg("Link: " + str(link))
        # Yield a new request for each link we found
        #for link in links:
        #    yield Request(url=link, callback=self.parse_page)