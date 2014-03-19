from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
from scrapy import log
import getpass
import sys
from os.path import basename
from urlparse import urlparse

class MoodleSpider(Spider):
    name = "moodle"
    allowed_domains = ["moodle.ucl.ac.uk"]
    start_urls = [
        "https://moodle.ucl.ac.uk/login/index.php"
    ]
    resource_path = "resources/"

    def parse(self, response):
        print "Please input your moodle login credentials."
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
                log.msg("Module link: " + str(link.extract()))
                yield Request(url=link.extract(), callback=self.parse_modulepage)

    def parse_modulepage(self, response):
        sel = Selector(response)
        log.msg("Parsing module page" + str(sel.xpath('//div[@id="ucl-sitename"]/text()').extract()))
        resources = sel.xpath('//li[@class="activity resource modtype_resource"]/div/div/a/@href')
        
        for resource in resources:
            log.msg("Downloading " + str(resource.extract()))
            yield Request(resource.extract(), callback=self.save_file)

    def save_file(self, response):
        path = self.get_resource_path(response.url)
        log.msg("Saving file: " + path)
        with open(path, "wb") as f:
            f.write(response.body)

    def get_resource_path(self, url):
        filepath = urlparse(url).path
        filename = basename(filepath)
        return self.resource_path + filename