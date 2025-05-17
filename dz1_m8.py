from collections import UserDict
from datetime import datetime, timedelta
import pickle
import os
from abc import ABC, abstractmethod

# Декоратор для обробки помилок введення
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (IndexError, ValueError) as e:
            return f"Error: {e}"
    return wrapper

# Абстрактний клас для інтерфейсу користувача
class UserInterface(ABC):
    @abstractmethod
    def display_contacts(self, contacts):
        pass

    @abstractmethod
    def display_message(self, message):
        pass

    @abstractmethod
    def display_commands(self):
        pass

# Конкретна реалізація для консолі
class ConsoleInterface(UserInterface):
    def display_contacts(self, contacts):
        if not contacts:
            self.display_message("No contacts found.")
        else:
            self.display_message('\n'.join(str(contact) for contact in contacts))

    def display_message(self, message):
        print(message)

    def display_commands(self):
        self.display_message("Available commands: hello, add, change, phone, delete, all, add-birthday, show-birthday, birthdays, close/exit")

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

# Клас для дня народження
class Birthday(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Invalid date format.")
        self.value = value

    def validate(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            return True
        except ValueError:
            return False
    
    def __str__(self):
        return self.value
    
    def to_datetime(self):
        return datetime.strptime(self.value, "%d.%m.%Y")

# Клас для запису контакту
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

# Клас адресної книги
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
                bd = record.birthday.to_datetime()
                current_year_bd = bd.replace(year=today.year).date()
                if current_year_bd < today:
                    next_bd = bd.replace(year=today.year + 1).date()
                else:
                    next_bd = current_year_bd

                delta = (next_bd - today).days
                if 0 <= delta <= 7:
                    if next_bd.weekday() == 5:
                        greeting_date = next_bd + timedelta(days=2)
                    elif next_bd.weekday() == 6:
                        greeting_date = next_bd + timedelta(days=1)
                    else:
                        greeting_date = next_bd
                    upcoming.append({"name": record.name.value, "birthday": greeting_date.strftime("%d.%m.%Y")})
        return upcoming

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())

# Функція для розбору введення
def parse_input(user_input):
    parts = user_input.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, args

# Обробники команд
@input_error
def delete_contact(args, book: AddressBook):
    name, *_ = args
    try:
        book.delete(name)
        return f"Contact {name} deleted."
    except ValueError:
        return f"Error: Contact {name} not found."

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

# Серіалізація
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return AddressBook()
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (EOFError, pickle.UnpicklingError):
        return AddressBook()

# Головна функція
def main():
    book = load_data()
    ui = ConsoleInterface()
    ui.display_message("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)
        
        if command in ["close", "exit"]:
            save_data(book)
            ui.display_message("Good bye!")
            break
        elif command == "hello":
            ui.display_message("How can I help you?")
        elif command == "add":
            ui.display_message(add_contact(args, book))
        elif command == "change":
            ui.display_message(change_contact(args, book))
        elif command == "phone":
            ui.display_message(get_phone(args, book))
        elif command == "delete":
            ui.display_message(delete_contact(args, book))
        elif command == "all":
            ui.display_contacts(book.data.values())
        elif command == "add-birthday":
            ui.display_message(add_birthday_cmd(args, book))
        elif command == "show-birthday":
            ui.display_message(show_birthday_cmd(args, book))
        elif command == "birthdays":
            ui.display_message(upcoming_birthdays(args, book))
        elif command == "commands":
            ui.display_commands()
        else:
            ui.display_message("Invalid command.")

if __name__ == "__main__":
    main()
