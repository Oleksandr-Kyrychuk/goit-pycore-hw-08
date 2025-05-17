import redis
import json
from models import Quote, Author
import re

# Налаштування Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def search_quotes():
    while True:
        command = input("Enter command (e.g., name:Steve Martin, tag:life, tags:life,live, exit): ")
        if command.lower() == 'exit':
            break

        try:
            cmd, value = command.split(':', 1)
            cache_key = f"{cmd}:{value}"
            cached_result = redis_client.get(cache_key)

            if cached_result:
                print("From cache:")
                print(cached_result)
                continue

            if cmd == 'name':
                regex = re.compile(f'^{value.lower()}', re.IGNORECASE)
                authors = Author.objects(fullname__iregex=regex)
                quotes = Quote.objects(author__in=authors)
                result = [str(quote.quote) for quote in quotes]

            elif cmd == 'tag':
                regex = re.compile(f'^{value.lower()}', re.IGNORECASE)
                quotes = Quote.objects(tags__iregex=regex)
                result = [str(quote.quote) for quote in quotes]

            elif cmd == 'tags':
                tags = value.split(',')
                regex = [re.compile(f'^{tag.lower()}', re.IGNORECASE) for tag in tags]
                quotes = Quote.objects(tags__in=[tag for regex in regex for tag in Quote.objects.tags.distinct() if
                                                 any(r.match(tag.lower()) for r in regex)])
                result = [str(quote.quote) for quote in quotes]

            else:
                print("Invalid command")
                continue

            result_str = '\n'.join(result).encode('utf-8').decode('utf-8')
            redis_client.setex(cache_key, 3600, result_str)  # Кеш на 1 годину
            print(result_str)

        except ValueError:
            print("Invalid format. Use: command:value")


if __name__ == '__main__':
    search_quotes()
