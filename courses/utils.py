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


def get_allowed_courses_for_user(user):
    """
    Returns QuerySet of Course objects for the given user:
    - Guests (Logged-out users): All published courses (for public catalog display).
    - Superusers/Global Admins: All published courses.
    - Authenticated users with an Institution (Institution Admins & Students): Only courses assigned to that institution directly or via category.
    - Authenticated users without an Institution: None (Course.objects.none()).
    """
    if not user or not user.is_authenticated:
        return Course.objects.filter(status='published')

    if user.is_superuser or getattr(user, 'role', '') == 'admin':
        return Course.objects.filter(status='published')

    inst = get_user_institution(user)
    if inst:
        allowed_course_ids = inst.allowed_courses.values_list('id', flat=True)
        allowed_category_ids = inst.allowed_categories.values_list('id', flat=True)

        return Course.objects.filter(
            models.Q(id__in=allowed_course_ids) |
            models.Q(category_id__in=allowed_category_ids),
            status='published'
        ).distinct()

    return Course.objects.none()


def get_allowed_categories_for_user(user):
    """
    Returns QuerySet of CourseCategory objects for the given user:
    - Guests: All active categories.
    - Superusers/Global Admins: All active categories.
    - Authenticated users with an Institution: Only categories assigned to that institution.
    """
    if not user or not user.is_authenticated:
        return CourseCategory.objects.filter(is_active=True).order_by('order', 'id')

    if user.is_superuser or getattr(user, 'role', '') == 'admin':
        return CourseCategory.objects.filter(is_active=True).order_by('order', 'id')

    inst = get_user_institution(user)
    if inst:
        allowed_category_ids = inst.allowed_categories.values_list('id', flat=True)
        return CourseCategory.objects.filter(id__in=allowed_category_ids, is_active=True).order_by('order', 'id')

    return CourseCategory.objects.none()


def is_course_accessible_by_user(user, course):
    """
    Check if a specific course's learning materials (lessons, videos, quizzes)
    are accessible by the given user.
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or getattr(user, 'role', '') == 'admin':
        return True

    inst = get_user_institution(user)
    if inst and course:
        allowed_course_ids = set(inst.allowed_courses.values_list('id', flat=True))
        allowed_cat_ids = set(inst.allowed_categories.values_list('id', flat=True))

        if course.id in allowed_course_ids or course.category_id in allowed_cat_ids:
            return True

    return False
