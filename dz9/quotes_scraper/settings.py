BOT_NAME = 'quotes_scraper'

SPIDER_MODULES = ['quotes_scraper.spiders']
NEWSPIDER_MODULE = 'quotes_scraper.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
    'quotes_scraper.pipelines.QuotesScraperPipeline': 300,
}

LOG_LEVEL = 'DEBUG'
LOG_ENABLED = True
LOG_STDOUT = True