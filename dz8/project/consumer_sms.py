import pika
from models import Contact
from bson import ObjectId


# Функція-заглушка для імітації надсилання SMS
def send_sms_stub(contact):
    print(f"Імітація надсилання SMS до {contact.fullname} на {contact.phone_number}")


# Налаштування підключення до RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Оголошення черги для SMS
channel.queue_declare(queue='sms_queue')


def callback(ch, method, properties, body):
    try:
        # Отримання ObjectID з повідомлення
        contact_id = ObjectId(body.decode())
        contact = Contact.objects(id=contact_id).first()

        if contact and not contact.message_sent:
            # Імітація надсилання SMS
            send_sms_stub(contact)
            # Оновлення статусу
            contact.message_sent = True
            contact.save()
            print(f"SMS успішно оброблено для {contact.fullname}")
        else:
            print(f"Контакт {contact_id} не знайдено або повідомлення вже надіслано")
    except Exception as e:
        print(f"Помилка при обробці SMS: {str(e)}")


# Налаштування споживача
channel.basic_consume(queue='sms_queue', on_message_callback=callback, auto_ack=True)

print("Споживач SMS запущено. Очікування повідомлень...")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("Споживач SMS зупинено")
finally:
    connection.close()