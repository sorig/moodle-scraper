from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
from scrapy import log
import getpass
import sys
from os.path import basename, join, exists, dirname
from os import makedirs
from urlparse import urlparse

class MoodleSpider(Spider):
    name = "moodle"
    allowed_domains = ["moodle.ucl.ac.uk"]
    start_urls = [
        "https://moodle.ucl.ac.uk/login/index.php"
    ]
    resource_path = "resources"

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
            courselinks = sel.xpath('//div[@class="content"]/ul/li/div/a')

            for link in courselinks:
                url = link.xpath('@href').extract()[0]

                request = Request(url=url, callback=self.parse_modulepage)
                # Pass on module name
                request.meta['moduleName'] = link.xpath('text()').extract()[0]

                log.msg("Module " + request.meta['moduleName'] + " link: " + url)
                yield request

    def parse_modulepage(self, response):
        sel = Selector(response)
        log.msg("Parsing module page: " + response.meta['moduleName'])

        sections = sel.xpath('//li[@class="section main clearfix"]')

        for section in sections:
            sectionName = section.xpath('.//h3[@class="sectionname"]/text()').extract()
            if len(sectionName) > 0:
                sectionName = sectionName[0]
                log.msg("Section: " + sectionName)
            else:
                sectionName = ""

            resources = section.xpath('.//li[@class="activity resource modtype_resource"]/div/div/a/@href')
            links = section.xpath('.//li[@class="activity url modtype_url"]/div/div/a/@href')
            for selector in [resources, links]:
                for resource in selector:
                    # make sure we get redirected to the content
                    url = resource.extract()+"&redirect=1"
                    yield self.request_resource(url, response.meta['moduleName'], sectionName)   

    def request_resource(self, url, moduleName, sectionName):
        log.msg("Downloading " + url)
        request = Request(url, callback=self.save_file)
        request.meta['moduleName'] = moduleName
        request.meta['sectionName'] = sectionName
        return request

    def save_file(self, response):
        path = self.get_resource_path(response.url, response.meta['moduleName'], response.meta['sectionName'])
        log.msg("Saving file: " + path)

        if not exists(dirname(path)):
            makedirs(dirname(path))

        with open(path, "wb") as f:
            f.write(response.body)

    def get_resource_path(self, url, moduleName, sectionName):
        filepath = urlparse(url).path
        fileName = basename(filepath)

        # Stupid heuristic. If incoming url ends with slash then it must be a website
        if fileName == "":
            fileName = "index.html"

        moduleName = self.path_encode(moduleName)
        sectionName = self.path_encode(sectionName)
        return join(self.resource_path, moduleName, sectionName, fileName)

    def path_encode(self, str):
        return str.replace(":", "-").replace("/", ":")