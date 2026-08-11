"""
Seed Script: Create Olympiad Entrance Exam Module Initial Data
- Olympiad Entrance Category
- Sample Entrance Exams with Instant, After 2 Hours, and Next Day Result Timing
- Multiple Question Types (MCQ, True/False, Multi-select, Numerical)
- Quiz Assignments via OlympiadQuiz bridge
"""

import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from olympiad.models import OlympiadCategory, Olympiad, OlympiadQuestion, OlympiadQuiz
from courses.models import Quiz

def seed_data():
    print("[INFO] Seeding Olympiad Entrance Exam Module Data...")

    # 1. Create Category
    category, created = OlympiadCategory.objects.get_or_create(name="Olympiad Entrance")
    print(f"[OK] Category '{category.name}' {'created' if created else 'already exists'}.")

    now = timezone.now()

    # 2. Create Olympiad Entrance Exams with configurable result timing modes
    exam1, _ = Olympiad.objects.get_or_create(
        name="National All India Olympiad Entrance 2026",
        category=category,
        defaults={
            'academic_year': '2026-27',
            'level': 'national',
            'class_group': 'Class 6-10',
            'fee': 0.00,
            'registration_start': now.date(),
            'registration_end': (now + timedelta(days=60)).date(),
            'exam_date': now + timedelta(days=7),
            'exam_duration_minutes': 60,
            'result_display_mode': 'immediate',  # Instant Result
            'result_timing_mode': 'immediate',
            'is_active': True,
        }
    )

    exam2, _ = Olympiad.objects.get_or_create(
        name="International STEM & AI Entrance Championship",
        category=category,
        defaults={
            'academic_year': '2026-27',
            'level': 'zonal',
            'class_group': 'Class 8-12',
            'fee': 100.00,
            'registration_start': now.date(),
            'registration_end': (now + timedelta(days=45)).date(),
            'exam_date': now + timedelta(days=5),
            'exam_duration_minutes': 90,
            'result_display_mode': 'after_2_hours',  # After 2 Hours
            'result_timing_mode': 'after_2_hours',
            'is_active': True,
        }
    )

    exam3, _ = Olympiad.objects.get_or_create(
        name="Junior Science & Cyber Entrance Talent Exam",
        category=category,
        defaults={
            'academic_year': '2026-27',
            'level': 'school',
            'class_group': 'Class 5-8',
            'fee': 50.00,
            'registration_start': now.date(),
            'registration_end': (now + timedelta(days=30)).date(),
            'exam_date': now + timedelta(days=3),
            'exam_duration_minutes': 45,
            'result_display_mode': 'next_day',  # Next Day
            'result_timing_mode': 'next_day',
            'next_day_release_time': '09:00:00',
            'is_active': True,
        }
    )

    print("[OK] Created 3 Entrance Exams with Instant, After 2 Hours, and Next Day Result Timing modes.")

    # 3. Add Multiple Question Types to Exam 1
    questions_data = [
        {
            'question_type': 'mcq',
            'question_text': 'What is the binary representation of the decimal number 13?',
            'option_a': '1100',
            'option_b': '1101',
            'option_c': '1110',
            'option_d': '1011',
            'correct_option': 'b',
            'explanation': '13 in binary is 1101 (8 + 4 + 0 + 1 = 13).',
            'difficulty': 'easy',
            'marks': 2,
        },
        {
            'question_type': 'true_false',
            'question_text': 'Python is a compiled language that produces bytecode executed by machine instructions directly without virtual machine.',
            'option_a': 'True',
            'option_b': 'False',
            'option_c': '',
            'option_d': '',
            'correct_option': 'b',
            'explanation': 'Python is an interpreted language executed line-by-line via the Python Virtual Machine (PVM).',
            'difficulty': 'medium',
            'marks': 2,
        },
        {
            'question_type': 'multi_select',
            'question_text': 'Which of the following are valid data structures in Computer Science?',
            'option_a': 'Stack',
            'option_b': 'Queue',
            'option_c': 'LinkedList',
            'option_d': 'Flowchart',
            'correct_option': 'a,b,c',
            'explanation': 'Stack, Queue, and LinkedList are linear data structures. Flowchart is a visual diagram.',
            'difficulty': 'hard',
            'marks': 3,
        },
        {
            'question_type': 'numerical',
            'question_text': 'Evaluate the mathematical expression: 4 * (12 - 5) + 6 / 2.',
            'option_a': '',
            'option_b': '',
            'option_c': '',
            'option_d': '',
            'correct_option': '31',
            'explanation': '4 * 7 + 3 = 28 + 3 = 31.',
            'difficulty': 'easy',
            'marks': 2,
        },
    ]

    for qd in questions_data:
        OlympiadQuestion.objects.get_or_create(
            olympiad=exam1,
            question_text=qd['question_text'],
            defaults=qd
        )
    print("[OK] Created MCQ, True/False, Multi-select, and Numerical Questions.")

    # 4. Assign Existing Quizzes if any
    available_quizzes = Quiz.objects.filter(is_active=True)[:2]
    for idx, quiz in enumerate(available_quizzes, start=1):
        OlympiadQuiz.objects.get_or_create(
            olympiad=exam1,
            quiz=quiz,
            defaults={
                'section_name': f"Section {idx+1}: {quiz.lesson.title if quiz.lesson else 'Special Quiz Section'}",
                'order': idx,
                'weightage_marks': 10,
            }
        )
    print("[OK] Quiz section assignment complete.")
    print("[SUCCESS] Seeding Completed Successfully!")

if __name__ == '__main__':
    seed_data()
