from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.http import FormRequest
from scrapy import log
import getpass
import sys
from os.path import basename, join, exists, dirname
from os import makedirs
from urlparse import urlparse, parse_qs

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
                query = parse_qs(urlparse(url).query)
                if "id" in query:
                    moduleId = query["id"][0]
                    resourceUrl = "https://moodle.ucl.ac.uk/course/resources.php?id=" + moduleId

                    request = Request(url=resourceUrl, callback=self.parse_resourcepage)

                    # Pass on module name
                    request.meta['moduleName'] = link.xpath('text()').extract()[0]

                    log.msg("Module " + request.meta['moduleName'] + " link: " + resourceUrl)
                    yield request

    def parse_resourcepage(self, response):
        sel = Selector(response)
        tablerows = sel.xpath('//table[@class="generaltable mod_index"]/tbody/tr')
        sectionName = "Top section"

        for row in tablerows:
            currentSectionName = row.xpath('.//td[@class="cell c0"]/text()').extract()
            if len(currentSectionName) > 0:
                sectionName = currentSectionName[0]

            link = row.xpath('.//a/@href').extract()
            if len(link) > 0:
                url = link[0]+"&redirect=1"
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
        if fileName == "" or not "." in fileName:
            fileName = "index.html"

        moduleName = self.path_encode(moduleName)
        sectionName = self.path_encode(sectionName)
        return join(self.resource_path, moduleName, sectionName, fileName)

    def path_encode(self, str):
        return str.replace(":", "-").replace("/", ":")