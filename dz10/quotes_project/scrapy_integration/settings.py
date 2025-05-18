BOT_NAME = 'scrapy_integration'
SPIDER_MODULES = ['scrapy_integration.spiders']
NEWSPIDER_MODULE = 'scrapy_integration.spiders'
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 0.5
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
ITEM_PIPELINES = {
    'scrapy_integration.pipelines.QuotesPipeline': 300,
}
TWISTED_REACTOR = 'twisted.internet.selectreactor.SelectReactor'