import json
import logging

logger = logging.getLogger(__name__)

class QuotesScraperPipeline:
    def open_spider(self, spider):
        self.quotes = []
        self.authors = []
        logger.info("Pipeline opened")

    def process_item(self, item, spider):
        logger.debug(f"Processing item: {item.__class__.__name__} - {dict(item)}")
        if item.__class__.__name__ == 'QuoteItem':
            self.quotes.append(dict(item))
        elif item.__class__.__name__ == 'AuthorItem':
            self.authors.append(dict(item))
        return item

    def close_spider(self, spider):
        logger.info(f"Saving {len(self.quotes)} quotes and {len(self.authors)} authors")
        try:
            with open('D:/goit-pycore-hw-08/dz9/quotes.json', 'w', encoding='utf-8') as f:
                json.dump(self.quotes, f, ensure_ascii=False, indent=2)
            with open('D:/goit-pycore-hw-08/dz9/authors.json', 'w', encoding='utf-8') as f:
                json.dump(self.authors, f, ensure_ascii=False, indent=2)
            logger.info("Files successfully saved")
        except Exception as e:
            logger.error(f"Error saving files: {str(e)}")