import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'quotes_project.settings')  # заміни quotes_project.settings на шлях до свого settings.py
django.setup()

import json
from pymongo import MongoClient
from quotes_app.models import Author, Quote, Tag
from django.contrib.auth.models import User



def migrate_data():
    # Підключення до MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['quotes_db']

    # Отримання даних
    authors_data = db.authors.find()
    quotes_data = db.quotes.find()

    # Створення суперадміна для created_by
    admin, _ = User.objects.get_or_create(username='admin', defaults={'is_superuser': True, 'is_staff': True})

    # Міграція авторів
    author_map = {}
    for author_data in authors_data:
        author, _ = Author.objects.get_or_create(
            fullname=author_data['fullname'],
            defaults={
                'born_date': author_data.get('born_date', ''),
                'born_location': author_data.get('born_location', ''),
                'description': author_data.get('description', '')
            }
        )
        author_map[author_data['fullname']] = author

    # Міграція цитат
    for quote_data in quotes_data:
        author = author_map.get(quote_data['author'])
        if not author:
            continue
        quote = Quote.objects.create(
            quote=quote_data['quote'],
            author=author,
            created_by=admin
        )
        for tag_name in quote_data['tags']:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            quote.tags.add(tag)

    print("Migration completed successfully")


if __name__ == '__main__':
    migrate_data()