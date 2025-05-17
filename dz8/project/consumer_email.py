import pika
from models import Contact
from bson import ObjectId


# Функція-заглушка для імітації надсилання email
def send_email_stub(contact):
    print(f"Імітація надсилання email до {contact.fullname} на {contact.email}")


# Налаштування підключення до RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Оголошення черги для email
channel.queue_declare(queue='email_queue')


def callback(ch, method, properties, body):
    try:
        # Отримання ObjectID з повідомлення
        contact_id = ObjectId(body.decode())
        contact = Contact.objects(id=contact_id).first()

        if contact and not contact.message_sent:
            # Імітація надсилання email
            send_email_stub(contact)
            # Оновлення статусу
            contact.message_sent = True
            contact.save()
            print(f"Email успішно оброблено для {contact.fullname}")
        else:
            print(f"Контакт {contact_id} не знайдено або повідомлення вже надіслано")
    except Exception as e:
        print(f"Помилка при обробці email: {str(e)}")


# Налаштування споживача
channel.basic_consume(queue='email_queue', on_message_callback=callback, auto_ack=True)

print("Споживач email запущено. Очікування повідомлень...")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("Споживач email зупинено")
finally:
    connection.close()