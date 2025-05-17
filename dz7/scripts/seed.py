import sys
import os

# Додаємо шлях до каталогу dz7, щоб імпорти типу 'from models.base' працювали
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from faker import Faker
from config import Session
from models.base import Base
from models.models import Group, Student, Teacher, Subject, Grade
from random import randint, choice
from datetime import datetime, timedelta
from config import engine

fake = Faker()


def seed_data():
    session = Session()

    # Create groups
    groups = [Group(name=f"Group-{i + 1}") for i in range(3)]
    session.add_all(groups)
    session.commit()

    # Create teachers
    teachers = [Teacher(fullname=fake.name()) for _ in range(5)]
    session.add_all(teachers)
    session.commit()

    # Create subjects
    subjects = [Subject(name=fake.word().capitalize(), teacher_id=choice(teachers).id) for _ in range(8)]
    session.add_all(subjects)
    session.commit()

    # Create students
    students = [Student(fullname=fake.name(), group_id=choice(groups).id) for _ in range(50)]
    session.add_all(students)
    session.commit()

    # Create grades
    for student in students:
        for _ in range(randint(10, 20)):
            date_received = fake.date_between(start_date="-1y", end_date="today")
            grade = Grade(
                student_id=student.id,
                subject_id=choice(subjects).id,
                grade=randint(60, 100),
                date_received=date_received
            )
            session.add(grade)
    session.commit()
    session.close()



if __name__ == "__main__":
    # Створюємо всі таблиці, якщо їх немає
    Base.metadata.create_all(bind=engine)

    # Заповнюємо базу даних тестовими даними
    seed_data()
    print("Database seeded successfully!")