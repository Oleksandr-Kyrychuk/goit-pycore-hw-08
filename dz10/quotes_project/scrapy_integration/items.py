import scrapy

class QuoteItem(scrapy.Item):
    quote = scrapy.Field()
    author_name = scrapy.Field()
    tags = scrapy.Field()
    created_by = scrapy.Field()  # Додано поле created_by

class AuthorItem(scrapy.Item):
    fullname = scrapy.Field()
    born_date = scrapy.Field()
    born_location = scrapy.Field()
    description = scrapy.Field()
    created_by = scrapy.Field()  # Додано поле created_by