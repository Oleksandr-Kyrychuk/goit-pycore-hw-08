import argparse
from config import Session
from models.models import Group, Student, Teacher, Subject, Grade
from sqlalchemy import func

def create_record(session, model, args):
    if model == Group:
        record = Group(name=args.name)
    elif model == Student:
        record = Student(fullname=args.name, group_id=args.group_id)
    elif model == Teacher:
        record = Teacher(fullname=args.name)
    elif model == Subject:
        record = Subject(name=args.name, teacher_id=args.teacher_id)
    elif model == Grade:
        record = Grade(student_id=args.student_id, subject_id=args.subject_id, grade=args.grade, date_received=args.date)
    session.add(record)
    session.commit()
    print(f"{model.__name__} created successfully!")

def list_records(session, model):
    records = session.query(model).all()
    for record in records:
        print(record.__dict__)

def update_record(session, model, args):
    record = session.query(model).filter_by(id=args.id).first()
    if record:
        if model == Group and args.name:
            record.name = args.name
        elif model == Student:
            if args.name:
                record.fullname = args.name
            if args.group_id:
                record.group_id = args.group_id
        elif model == Teacher and args.name:
            record.fullname = args.name
        elif model == Subject:
            if args.name:
                record.name = args.name
            if args.teacher_id:
                record.teacher_id = args.teacher_id
        elif model == Grade:
            if args.student_id:
                record.student_id = args.student_id
            if args.subject_id:
                record.subject_id = args.subject_id
            if args.grade:
                record.grade = args.grade
            if args.date:
                record.date_received = args.date
        session.commit()
        print(f"{model.__name__} updated successfully!")
    else:
        print(f"{model.__name__} with id={args.id} not found!")

def remove_record(session, model, args):
    record = session.query(model).filter_by(id=args.id).first()
    if record:
        session.delete(record)
        session.commit()
        print(f"{model.__name__} removed successfully!")
    else:
        print(f"{model.__name__} with id={args.id} not found!")

def main():
    parser = argparse.ArgumentParser(description="CLI for CRUD operations on school database")
    parser.add_argument('-a', '--action', required=True, choices=['create', 'list', 'update', 'remove'], help="Action to perform")
    parser.add_argument('-m', '--model', required=True, choices=['Group', 'Student', 'Teacher', 'Subject', 'Grade'], help="Model to operate on")
    parser.add_argument('--id', type=int, help="ID of the record")
    parser.add_argument('--name', help="Name or fullname of the record")
    parser.add_argument('--group_id', type=int, help="Group ID for Student or Grade")
    parser.add_argument('--teacher_id', type=int, help="Teacher ID for Subject")
    parser.add_argument('--student_id', type=int, help="Student ID for Grade")
    parser.add_argument('--subject_id', type=int, help="Subject ID for Grade")
    parser.add_argument('--grade', type=float, help="Grade value")
    parser.add_argument('--date', help="Date for Grade (YYYY-MM-DD)")

    args = parser.parse_args()
    session = Session()

    model_map = {
        'Group': Group,
        'Student': Student,
        'Teacher': Teacher,
        'Subject': Subject,
        'Grade': Grade
    }
    model = model_map[args.model]

    if args.action == 'create':
        create_record(session, model, args)
    elif args.action == 'list':
        list_records(session, model)
    elif args.action == 'update':
        update_record(session, model, args)
    elif args.action == 'remove':
        remove_record(session, model, args)

    session.close()

if __name__ == "__main__":
    main()