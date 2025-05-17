import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker()

# Connect to SQLite database
conn = sqlite3.connect('university.db')
cursor = conn.cursor()

# Create tables
cursor.executescript('''
CREATE TABLE IF NOT EXISTS groups (
    group_id INTEGER PRIMARY KEY,
    group_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id INTEGER PRIMARY KEY,
    teacher_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY,
    student_name TEXT NOT NULL,
    group_id INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id INTEGER PRIMARY KEY,
    subject_name TEXT NOT NULL,
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

CREATE TABLE IF NOT EXISTS grades (
    grade_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    subject_id INTEGER,
    grade INTEGER,
    date_received DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
''')

# Generate data
# Groups
groups = [(i, f'Group-{chr(65+i)}') for i in range(3)]
cursor.executemany('INSERT INTO groups (group_id, group_name) VALUES (?, ?)', groups)

# Teachers
teachers = [(i, fake.name()) for i in range(1, 6)]
cursor.executemany('INSERT INTO teachers (teacher_id, teacher_name) VALUES (?, ?)', teachers)

# Subjects
subjects = [(i, fake.word().capitalize() + " Studies", random.randint(1, 5)) for i in range(1, 7)]
cursor.executemany('INSERT INTO subjects (subject_id, subject_name, teacher_id) VALUES (?, ?, ?)', subjects)

# Students
students = []
for i in range(1, 51):
    students.append((i, fake.name(), random.randint(1, 3)))
cursor.executemany('INSERT INTO students (student_id, student_name, group_id) VALUES (?, ?, ?)', students)

# Grades
grades = []
grade_id = 1
for student_id in range(1, 51):
    for _ in range(random.randint(15, 20)):
        subject_id = random.randint(1, 6)
        grade = random.randint(60, 100)
        date_received = fake.date_between(start_date='-1y', end_date='today')
        grades.append((grade_id, student_id, subject_id, grade, date_received))
        grade_id += 1
cursor.executemany('INSERT INTO grades (grade_id, student_id, subject_id, grade, date_received) VALUES (?, ?, ?, ?, ?)', grades)

# Commit and close
conn.commit()
conn.close()

print("Database created and populated successfully!")

# --- QUERY FILE GENERATION SECTION ---
# After running once to create query files, comment out or delete this section
# to prevent overwriting files on subsequent runs.

queries = {
    "query_1.sql": """
SELECT s.student_name, ROUND(AVG(g.grade), 2) as avg_grade
FROM students s
JOIN grades g ON s.student_id = g.student_id
GROUP BY s.student_id, s.student_name
ORDER BY avg_grade DESC
LIMIT 5;
""",
    "query_2.sql": """
SELECT s.student_name, ROUND(AVG(g.grade), 2) as avg_grade
FROM students s
JOIN grades g ON s.student_id = g.student_id
WHERE g.subject_id = 1
GROUP BY s.student_id, s.student_name
ORDER BY avg_grade DESC
LIMIT 1;
""",
    "query_3.sql": """
SELECT gr.group_name, ROUND(AVG(g.grade), 2) as avg_grade
FROM groups gr
JOIN students s ON gr.group_id = s.group_id
JOIN grades g ON s.student_id = g.student_id
WHERE g.subject_id = 1
GROUP BY gr.group_id, gr.group_name;
""",
    "query_4.sql": """
SELECT ROUND(AVG(grade), 2) as avg_grade
FROM grades;
""",
    "query_5.sql": """
SELECT sub.subject_name
FROM subjects sub
WHERE sub.teacher_id = 1;
""",
    "query_6.sql": """
SELECT s.student_name
FROM students s
WHERE s.group_id = 1;
""",
    "query_7.sql": """
SELECT s.student_name, g.grade
FROM students s
JOIN grades g ON s.student_id = g.student_id
WHERE s.group_id = 1 AND g.subject_id = 1;
""",
    "query_8.sql": """
SELECT ROUND(AVG(g.grade), 2) as avg_grade
FROM grades g
JOIN subjects sub ON g.subject_id = sub.subject_id
WHERE sub.teacher_id = 1;
""",
    "query_9.sql": """
SELECT DISTINCT sub.subject_name
FROM subjects sub
JOIN grades g ON sub.subject_id = g.subject_id
WHERE g.student_id = 1;
""",
    "query_10.sql": """
SELECT sub.subject_name
FROM subjects sub
JOIN grades g ON sub.subject_id = g.subject_id
WHERE g.student_id = 1 AND sub.teacher_id = 1;
""",
    "query_11.sql": """
SELECT ROUND(AVG(g.grade), 2) as avg_grade
FROM grades g
JOIN subjects sub ON g.subject_id = sub.subject_id
WHERE g.student_id = 1 AND sub.teacher_id = 1;
""",
    "query_12.sql": """
SELECT s.student_name, g.grade
FROM students s
JOIN grades g ON s.student_id = g.student_id
WHERE s.group_id = 1 AND g.subject_id = 1
AND g.date_received = (
    SELECT MAX(date_received)
    FROM grades g2
    WHERE g2.subject_id = 1 AND g2.student_id IN (
        SELECT student_id FROM students WHERE group_id = 1
    )
);
"""
}

for filename, query in queries.items():
    with open(filename, 'w') as f:
        f.write(query.strip())

print("Query files created successfully!")

# --- END QUERY FILE GENERATION SECTION ---