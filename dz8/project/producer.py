import pika
from faker import Faker
from models import Contact
import random

# Ініціалізація Faker для генерації фейкових даних
fake = Faker()

# Налаштування підключення до RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Оголошення черг для email і SMS
channel.queue_declare(queue='email_queue')
channel.queue_declare(queue='sms_queue')


def generate_contacts(num_contacts=10):
    for _ in range(num_contacts):
        # Генерація фейкового контакту
        contact = Contact(
            fullname=fake.name(),
            email=fake.email(),
            phone_number=fake.phone_number(),
            preferred_method=random.choice(['email', 'sms'])
        )
        contact.save()

        # Відправлення ObjectID контакту в потрібну чергу
        queue_name = 'email_queue' if contact.preferred_method == 'email' else 'sms_queue'
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=str(contact.id)
        )
        print(f"Відправлено {contact.fullname} ({contact.preferred_method}) до {queue_name}")


try:
    # Генерація 10 контактів
    generate_contacts(10)
    print("Усі контакти згенеровано та відправлено до черг")
finally:
    # Закриття підключення до RabbitMQ
    connection.close()