import json
import re
from mongoengine import Document, StringField, DateTimeField, ListField, ReferenceField, connect
from datetime import datetime
import redis
import pymongo

# Налаштування підключення до MongoDB Atlas
connect(
    db='quotes_db',
    host='mongodb+srv://2342:pass@cluster0.qvyok.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
)


# Налаштування підключення до Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Модель для авторів
class Author(Document):
    fullname = StringField(required=True, unique=True)
    born_date = StringField()
    born_location = StringField()
    description = StringField()

    meta = {'collection': 'authors'}

# Модель для цитат
class Quote(Document):
    tags = ListField(StringField())
    author = ReferenceField(Author, required=True)
    quote = StringField(required=True)

    meta = {'collection': 'quotes'}

# Функція для завантаження даних з JSON файлів
def load_json_data():
    # Завантаження авторів
    with open('authors.json', 'r', encoding='utf-8') as f:
        authors_data = json.load(f)

    for author_data in authors_data:
        author = Author(**author_data)
        author.save()

    # Завантаження цитат
    with open('quotes.json', 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)

    for quote_data in quotes_data:
        author = Author.objects(fullname=quote_data['author']).first()
        if author:
            quote = Quote(
                tags=quote_data['tags'],
                author=author,
                quote=quote_data['quote']
            )
            quote.save()

# Функція для пошуку цитат
def search_quotes(command, value):
    cache_key = f"{command}:{value}"

    # Перевірка кешу
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # Обробка різних типів команд
    results = []

    if command == 'name':
        # Пошук за повним або частковим ім'ям автора
        authors = Author.objects(fullname__iregex=re.compile(f'^{value}', re.IGNORECASE))
        for author in authors:
            quotes = Quote.objects(author=author)
            for quote in quotes:
                results.append({
                    'quote': quote.quote,
                    'author': author.fullname,
                    'tags': quote.tags
                })

    elif command == 'tag':
        # Пошук за одним тегом (частковий збіг)
        quotes = Quote.objects(tags__iregex=re.compile(f'^{value}', re.IGNORECASE))
        for quote in quotes:
            results.append({
                'quote': quote.quote,
                'author': quote.author.fullname,
                'tags': quote.tags
            })

    elif command == 'tags':
        # Пошук за кількома тегами
        tags = value.split(',')
        quotes = Quote.objects(tags__in=tags)
        for quote in quotes:
            results.append({
                'quote': quote.quote,
                'author': quote.author.fullname,
                'tags': quote.tags
            })

    # Збереження результатів у кеш (на 1 годину)
    if results:
        redis_client.setex(cache_key, 3600, json.dumps(results))

    return results

# Головна функція для інтерактивного пошуку
def main():
    # Завантаження даних при запуску
    load_json_data()

    while True:
        try:
            user_input = input("Введіть команду (наприклад, name:Steve Martin, tag:life, tags:life,live, exit): ")
            if user_input.lower() == 'exit':
                break

            if ':' not in user_input:
                print("Неправильний формат команди. Використовуйте формат команда:значення")
                continue

            command, value = user_input.split(':', 1)
            command = command.strip().lower()
            value = value.strip()

            if command not in ['name', 'tag', 'tags']:
                print("Невідома команда. Доступні команди: name, tag, tags, exit")
                continue

            results = search_quotes(command, value)

            if not results:
                print("Цитати не знайдено")
            else:
                for result in results:
                    print(f"\nЦитата: {result['quote']}")
                    print(f"Автор: {result['author']}")
                    print(f"Теги: {', '.join(result['tags'])}")
                    print("-" * 50)

        except Exception as e:
            print(f"Сталася помилка: {str(e)}")

if __name__ == "__main__":
    main()