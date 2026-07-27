"""
Courses URLs Configuration
JSON API only — categories, courses, modules, lessons, quizzes/questions,
quiz-taking flow, and enrollments.
"""

from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # ========================================================================
    # CATEGORIES
    # ========================================================================
    path('categories/', views.category_list, name='category-list'),
    path('categories/<int:pk>/', views.category_detail, name='category-detail'),

    # ========================================================================
    # COURSES
    # ========================================================================
    path('courses/', views.course_list, name='course-list'),
    path('courses/<slug:slug>/', views.course_detail, name='course-detail'),
    path('courses/<slug:slug>/enroll/', views.enroll_course, name='course-enroll'),

    # ========================================================================
    # MODULES
    # ========================================================================
    path('courses/<slug:slug>/modules/', views.module_list, name='module-list'),
    path('modules/<int:pk>/', views.module_detail, name='module-detail'),

    # ========================================================================
    # LESSONS
    # ========================================================================
    path('modules/<int:pk>/lessons/', views.lesson_list, name='lesson-list'),
    path('lessons/<int:pk>/', views.lesson_detail, name='lesson-detail'),
    path('lessons/<int:pk>/quiz/', views.lesson_quiz, name='lesson-quiz'),

    # ========================================================================
    # QUIZZES & QUESTIONS
    # ========================================================================
    path('quizzes/<int:pk>/', views.quiz_detail, name='quiz-detail'),
    path('quizzes/<int:pk>/questions/', views.question_list, name='question-list'),
    path('questions/<int:pk>/', views.question_detail, name='question-detail'),
    path('quizzes/<int:pk>/access-logs/', views.quiz_access_logs, name='quiz-access-logs'),

    # ========================================================================
    # QUIZ-TAKING FLOW
    # ========================================================================
    path('quizzes/<int:pk>/start/', views.start_attempt, name='quiz-start'),
    path('attempts/<int:pk>/answer/', views.submit_answer, name='attempt-answer'),
    path('attempts/<int:pk>/submit/', views.submit_attempt, name='attempt-submit'),
    path('attempts/<int:pk>/', views.attempt_detail, name='attempt-detail'),
    path('my-attempts/', views.my_attempts, name='my-attempts'),

    # ========================================================================
    # ENROLLMENTS
    # ========================================================================
    path('my-enrollments/', views.my_enrollments, name='my-enrollments'),
    path('enrollments/<int:pk>/progress/', views.update_progress, name='enrollment-progress'),
]