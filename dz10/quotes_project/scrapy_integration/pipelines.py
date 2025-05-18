from scrapy_integration.items import AuthorItem, QuoteItem
from quotes_app.models import Author, Quote, Tag
from twisted.internet.threads import deferToThread
import logging

logger = logging.getLogger(__name__)


class QuotesPipeline:
    def process_item(self, item, spider):
        logger.info("Processing item: %s", type(item))
        if isinstance(item, AuthorItem):
            return deferToThread(self.process_author_item, item, spider)
        if isinstance(item, QuoteItem):
            return deferToThread(self.process_quote_item, item, spider)
        return item

    def process_author_item(self, item, spider):
        logger.info("Processing author: %s", item['fullname'])
        defaults = {
            'born_date': item['born_date'],
            'born_location': item['born_location'],
            'description': item['description'],
        }
        if 'created_by' in item:
            defaults['created_by'] = item['created_by']
        author, created = Author.objects.get_or_create(
            fullname=item['fullname'],
            defaults=defaults
        )
        logger.info("Author %s, created: %s", author.fullname, created)
        return item

    def process_quote_item(self, item, spider):
        logger.info("Processing quote: %s", item['quote'])
        author = Author.objects.filter(fullname=item['author_name']).first()
        if not author:
            logger.warning("Author not found: %s", item['author_name'])
            return item

        defaults = {'author': author}
        if 'created_by' in item:
            defaults['created_by'] = item['created_by']
        else:
            logger.warning("No 'created_by' field in QuoteItem, skipping user assignment")

        quote, created = Quote.objects.get_or_create(
            quote=item['quote'],
            defaults=defaults
        )
        logger.info("Quote %s, created: %s", quote.quote, created)

        for tag_name in item['tags']:
            tag, tag_created = Tag.objects.get_or_create(name=tag_name)
            tag.quotes.add(quote)  # Змінено з quote.tags.add(tag)
            logger.info("Added quote to tag %s, created: %s", tag_name, tag_created)

        logger.info("Saved quote: %s", quote.quote)
        return item