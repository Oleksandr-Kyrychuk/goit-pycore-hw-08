import json
from models import Author, Quote


def upload_to_mongodb():
    # Завантаження авторів
    with open('authors.json', 'r', encoding='utf-8') as f:
        authors_data = json.load(f)

    Author.objects.delete()  # Очищення колекції
    author_map = {}
    for author_data in authors_data:
        author = Author(**author_data).save()
        author_map[author.fullname] = author

    # Завантаження цитат
    with open('quotes.json', 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)

    Quote.objects.delete()  # Очищення колекції
    for quote_data in quotes_data:
        author_name = quote_data.pop('author')
        quote_data['author'] = author_map[author_name]
        Quote(**quote_data).save()

    print("Data successfully uploaded to MongoDB")


if __name__ == '__main__':
    upload_to_mongodb()