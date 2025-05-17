from mongoengine import Document, StringField, BooleanField, connect

# Налаштування підключення до MongoDB Atlas
connect(
    db='quotes_db',
    host='mongodb+srv://<your_username>:<your_password>@cluster0.<your_cluster_id>.mongodb.net/quotes_db?retryWrites=true&w=majority',
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
    serverSelectionTimeoutMS=30000
)


class Contact(Document):
    fullname = StringField(required=True)
    email = StringField(required=True)
    phone_number = StringField()
    preferred_method = StringField(choices=['email', 'sms'], default='email')
    message_sent = BooleanField(default=False)

    meta = {'collection': 'contacts'}