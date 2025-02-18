from collections import UserDict
from datetime import datetime, timedelta
import pickle
import os

# Декоратор для обробки помилок введення
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (IndexError, ValueError) as e:
            return f"Error: {e}"
    return wrapper

# Базовий клас для полів
class Field:
    def __init__(self, value):
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __str__(self):
        return str(self.value)

# Клас для імені (не може бути порожнім)
class Name(Field):
    def __init__(self, value):
        if not value.strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value)

# Клас для телефону (має бути 10 цифр)
class Phone(Field):
    def __init__(self, value):
        self._validate(value)
        super().__init__(value)

    def _validate(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must be 10 digits.")

# Клас для дня народження: перевіряємо формат та перетворюємо рядок на datetime
class Birthday(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Invalid date format.")
        self.value = value  # зберігаємо значення як рядок

    def validate(self, value):
        try:
            # Перевіряємо правильність формату
            datetime.strptime(value, "%d.%m.%Y")
            return True
        except ValueError:
            return False
    
    def __str__(self):
        return self.value  # Повертаємо значення у вигляді рядка
    
    def to_datetime(self):
        # Перетворюємо значення в datetime для обчислень
        return datetime.strptime(self.value, "%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))
    
    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)
    
    def remove_phone(self, phone):
        phone_to_remove = next((p for p in self.phones if p.value == phone), None)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError("Phone number not found.")

    def edit_phone(self, old_phone, new_phone):
        if not self.find_phone(old_phone):
            raise ValueError("Phone number not found.")
        self.add_phone(new_phone)       
        self.remove_phone(old_phone)

    def find_phone(self, phone):
        return next((p for p in self.phones if p.value == phone), None)

    def __str__(self):
        birthday_str = f", Birthday: {self.birthday}" if self.birthday else ""
        phones_str = ", ".join(str(p) for p in self.phones)
        return f"Contact name: {self.name}, Phones: {phones_str}{birthday_str}"

# Клас AddressBook, який містить записи (Record) у вигляді словника
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError("Record not found.")

    def get_upcoming_birthdays(self):
        upcoming = []
        today = datetime.now().date()
        for record in self.data.values():
            if record.birthday:
                bd = record.birthday.to_datetime()  # Перетворюємо рядок на datetime
                current_year_bd = bd.replace(year=today.year).date()  # Використовуємо datetime для маніпуляцій
                if current_year_bd < today:
                    next_bd = bd.replace(year=today.year + 1).date()
                else:
                    next_bd = current_year_bd

                delta = (next_bd - today).days
                if 0 <= delta <= 7:
                    # Якщо наступний день народження припадає на вихідний, переносимо привітання на понеділок
                    if next_bd.weekday() == 5:  # субота
                        greeting_date = next_bd + timedelta(days=2)
                    elif next_bd.weekday() == 6:  # неділя
                        greeting_date = next_bd + timedelta(days=1)
                    else:
                        greeting_date = next_bd
                    upcoming.append({"name": record.name.value, "birthday": greeting_date.strftime("%d.%m.%Y")})
        return upcoming


    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())

# Функція для розбору введення користувача
def parse_input(user_input):
    parts = user_input.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, args
#Функція видалення 
@input_error
def delete_contact(args, book: AddressBook):
    name, *_ = args
    try:
        book.delete(name)
        return f"Contact {name} deleted."
    except ValueError:
        return f"Error: Contact {name} not found."

# Функції-обробники команд з декоратором для помилок
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Changed phone for {name}: {old_phone} -> {new_phone}"
    else:
        return f"Contact {name} not found."

@input_error
def get_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record:
        return f"Phones for {name}: {', '.join(str(p) for p in record.phones)}"
    else:
        return f"Contact {name} not found."

@input_error
def add_birthday_cmd(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Added birthday {birthday} for {name}"
    else:
        return f"Contact {name} not found."

@input_error
def show_birthday_cmd(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday}"
    else:
        return f"Birthday not found for {name}."

@input_error
def upcoming_birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        result = "Upcoming birthdays:\n"
        for entry in upcoming:
            result += f"{entry['name']}: {entry['birthday']}\n"
        return result
    else:
        return "No birthdays in the next 7 days."

#серіалізація
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return AddressBook()  # Якщо файл відсутній або порожній, повертаємо нову адресну книгу
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (EOFError, pickle.UnpicklingError):
        return AddressBook()  # Якщо файл пошкоджений, повертаємо нову книгу



def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)
        
        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(get_phone(args, book))
        elif command == "delete":
            print(delete_contact(args, book))
        elif command == "all":
            print(book)
        elif command == "add-birthday":
            print(add_birthday_cmd(args, book))
        elif command == "show-birthday":
            print(show_birthday_cmd(args, book))
        elif command == "birthdays":
            print(upcoming_birthdays(args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
