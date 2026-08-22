"""
Course Permission & Institution Access Helpers
"""

from django.db import models
from courses.models import Course, CourseCategory


def get_user_institution(user):
    """Fetch the institution associated with a given user (either admin or student)."""
    if not user or not user.is_authenticated:
        return None

    from institutions.models import Institution
    inst = Institution.objects.filter(admin_user=user).first()

    if not inst and hasattr(user, 'student_profile') and user.student_profile and user.student_profile.institution:
        inst = user.student_profile.institution

    return inst


def get_allowed_courses_for_user(user, exclude_books=True):
    """
    Returns QuerySet of Course objects so every user (guests, students, institution admins)
    can browse and view the full course catalog on the main website.
    Staff/Admins see all courses regardless of status.
    """
    if user and user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, 'role', '') in ('admin', 'superadmin', 'super_admin', 'main_admin', 'staff')):
        qs = Course.objects.all()
    else:
        qs = Course.objects.filter(status='published')
    return qs.exclude(category__slug='ai-books') if exclude_books else qs


def get_allowed_categories_for_user(user, exclude_books=True):
    """
    Returns QuerySet of ALL active CourseCategory objects for catalog browsing.
    """
    qs = CourseCategory.objects.filter(is_active=True).order_by('order', 'id')
    return qs.exclude(slug='ai-books') if exclude_books else qs


def is_course_accessible_by_user(user, course):
    """
    Check if a specific course's learning materials (lessons, videos, quizzes, ebook reader)
    are accessible by the given user (login + enrollment or institution allotment required).
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff or getattr(user, 'role', '') in ('admin', 'super_admin', 'staff'):
        return True

    from courses.models import Enrollment
    if Enrollment.objects.filter(student=user, course=course).exists():
        return True

    inst = get_user_institution(user)
    if inst and course:
        allowed_course_ids = set(inst.allowed_courses.values_list('id', flat=True))
        allowed_cat_ids = set(inst.allowed_categories.values_list('id', flat=True))

        if course.id in allowed_course_ids or course.category_id in allowed_cat_ids:
            return True

    return False
