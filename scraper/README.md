# Moodle scraper

Download all resource files from your moodle page

## Running the scraper

Requires: [virtualenv](http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation)

Switch to virtual environment:
```
source venv/bin/activate
```
Change to scraper directory and crawl moodle:
```
cd scraper
scrapy crawl moodle
```

Type in your login credentials when prompted.
Your resource files will be stored under `moodle-scraper/scraper/resources`