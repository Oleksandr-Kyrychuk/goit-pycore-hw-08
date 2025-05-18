import os
import django
import scrapy
from scrapy import signals
from scrapy_integration.items import QuoteItem, AuthorItem
import logging

# Ініціалізація Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quotes_project.settings')
logger = logging.getLogger(__name__)
logger.info("Starting Django setup")
django.setup()
logger.info("Django setup completed")

from quotes_app.models import Author, Quote, Tag
from django.contrib.auth.models import User

class QuotesSpider(scrapy.Spider):
    name = 'quotes'
    start_urls = ['http://quotes.toscrape.com']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Initializing QuotesSpider with start_urls: %s", self.start_urls)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        logger.warning("Spider finished crawling.")

    def parse(self, response):
        logger.warning("!!! START PARSING PAGE: %s !!!", response.url)
        logger.info("Response status: %s", response.status)
        logger.info("Response headers: %s", response.headers)
        if response.status != 200:
            logger.error("Failed to fetch page: %s", response.url)
            return

        try:
            admin = User.objects.get(username='admin')
            logger.info("Admin user found: %s", admin.username)
        except User.DoesNotExist:
            logger.error("Admin user not found. Please create a superuser with username='admin'.")
            return

        quotes_found = False
        for quote in response.css('div.quote'):
            quotes_found = True
            quote_item = QuoteItem()
            quote_item['quote'] = quote.css('span.text::text').get()
            quote_item['author_name'] = quote.css('small.author::text').get()
            quote_item['tags'] = quote.css('div.tags a.tag::text').getall()
            quote_item['created_by'] = admin  # Змінено з 'admin' на 'created_by'
            logger.info("Found quote: %s by %s", quote_item['quote'], quote_item['author_name'])

            # Перевірка автора
            author = Author.objects.filter(fullname=quote_item['author_name']).first()
            if not author:
                author_url = quote.css('a[href*="author"]::attr(href)').get()
                if author_url:
                    logger.info("Following author URL: %s", author_url)
                    yield response.follow(author_url, callback=self.parse_author, meta={'quote_item': quote_item})
                continue

            # Передача цитати до pipeline
            yield quote_item

        if not quotes_found:
            logger.warning("No quotes found on page: %s", response.url)
            logger.info("Response body preview: %s", response.text[:500])

        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            logger.info("Following next page: %s", next_page)
            yield response.follow(next_page, callback=self.parse)

    def parse_author(self, response):
        logger.info("Parsing author page: %s", response.url)
        logger.info("Response status: %s", response.status)
        quote_item = response.meta.get('quote_item')
        author_item = AuthorItem()
        author_item['fullname'] = response.css('h3.author-title::text').get().strip()
        author_item['born_date'] = response.css('span.author-born-date::text').get() or ''
        author_item['born_location'] = response.css('span.author-born-location::text').get() or ''
        author_item['description'] = response.css('div.author-description::text').get().strip() or ''
        logger.info("Found author: %s", author_item['fullname'])

        try:
            admin = User.objects.get(username='admin')
            logger.info("Admin user found for author: %s", admin.username)
        except User.DoesNotExist:
            logger.error("Admin user not found. Please create a superuser with username='admin'.")
            return

        author_item['created_by'] = admin  # Змінено з 'admin' на 'created_by'
        # Передача автора до pipeline
        yield author_item

        # Якщо є цитата, передати її до pipeline
        if quote_item:
            quote_item['author_name'] = author_item['fullname']
            yield quote_item