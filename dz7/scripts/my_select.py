from sqlalchemy import func, desc
from config import Session
from models.models import Student, Group, Teacher, Subject, Grade

def select_1():
    session = Session()
    result = session.query(Student.fullname, func.round(func.avg(Grade.grade), 2).label('avg_grade'))\
        .select_from(Grade).join(Student).group_by(Student.id).order_by(desc('avg_grade')).limit(5).all()
    session.close()
    return result

def select_2(subject_id):
    session = Session()
    result = session.query(Student.fullname, func.round(func.avg(Grade.grade), 2).label('avg_grade'))\
        .select_from(Grade).join(Student).filter(Grade.subject_id == subject_id)\
        .group_by(Student.id).order_by(desc('avg_grade')).limit(1).all()
    session.close()
    return result

def select_3(subject_id):
    session = Session()
    result = session.query(Group.name, func.round(func.avg(Grade.grade), 2).label('avg_grade'))\
        .select_from(Grade).join(Student).join(Group).filter(Grade.subject_id == subject_id)\
        .group_by(Group.id).all()
    session.close()
    return result

def select_4():
    session = Session()
    result = session.query(func.round(func.avg(Grade.grade), 2).label('avg_grade'))\
        .select_from(Grade).scalar()
    session.close()
    return [(None, result)]

def select_5(teacher_id):
    session = Session()
    result = session.query(Subject.name)\
        .filter(Subject.teacher_id == teacher_id).all()
    session.close()
    return [(name,) for name in result]

def select_6(group_id):
    session = Session()
    result = session.query(Student.fullname)\
        .filter(Student.group_id == group_id).all()
    session.close()
    return [(name,) for name in result]

def select_7(group_id, subject_id):
    session = Session()
    result = session.query(Student.fullname, Grade.grade)\
        .select_from(Grade).join(Student).filter(Student.group_id == group_id, Grade.subject_id == subject_id).all()
    session.close()
    return result

def select_8(teacher_id):
    session = Session()
    result = session.query(func.round(func.avg(Grade.grade), 2).label('avg_grade'))\
        .select_from(Grade).join(Subject).filter(Subject.teacher_id == teacher_id).scalar()
    session.close()
    return [(None, result)]

def select_9(student_id):
    session = Session()
    result = session.query(Subject.name)\
        .select_from(Grade).join(Subject).filter(Grade.student_id == student_id).distinct().all()
    session.close()
    return [(name,) for name in result]

def select_10(student_id, teacher_id):
    session = Session()
    result = session.query(Subject.name)\
        .select_from(Grade).join(Subject).filter(Grade.student_id == student_id, Subject.teacher_id == teacher_id)\
        .distinct().all()
    session.close()
    return [(name,) for name in result]

def select_11(teacher_id, student_id):
    session = Session()
    result = session.query(func.round(func.avg(Grade.grade), 2).label('avg_grade'))\
        .select_from(Grade).join(Subject).filter(Subject.teacher_id == teacher_id, Grade.student_id == student_id)\
        .scalar()
    session.close()
    return [(None, result)]

def select_12(group_id, subject_id):
    session = Session()
    subquery = session.query(func.max(Grade.date_received).label('max_date'))\
        .filter(Grade.subject_id == subject_id).scalar_subquery()
    result = session.query(Student.fullname, Grade.grade)\
        .select_from(Grade).join(Student).filter(
            Student.group_id == group_id,
            Grade.subject_id == subject_id,
            Grade.date_received == subquery
        ).all()
    session.close()
    return result