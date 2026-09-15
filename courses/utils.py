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


def get_allowed_courses_for_user(user, exclude_books=True, only_books=False, only_allowed=False):
    """
    Returns QuerySet of Course objects.
    - If only_allowed=True (Admin Dashboard / My Enrolled Courses):
        - Super Admin / Staff: All courses.
        - Institution Users / Admins: ONLY courses allotted to their Institution.
        - Students: ONLY courses they are enrolled in.
    - If only_allowed=False (Public Website Catalog & Homepage for every login):
        - Super Admin / Staff: All courses.
        - Every User / Institution / Student / Visitor: All published courses (available for purchase on website).
    """
    if not user or not user.is_authenticated:
        qs = Course.objects.filter(status='published')
    else:
        user_role = (getattr(user, 'role', '') or '').lower().strip()
        is_main_admin = user.is_superuser or user.is_staff or user_role in ('admin', 'superadmin', 'super_admin', 'main_admin', 'staff')

        if is_main_admin:
            qs = Course.objects.all()
        elif only_allowed:
            if user_role in ('institution', 'institution_admin', 'school', 'college', 'coaching'):
                inst = get_user_institution(user)
                if inst:
                    allowed_course_ids = set(inst.allowed_courses.values_list('id', flat=True))
                    allowed_cat_ids = set(inst.allowed_categories.values_list('id', flat=True))
                    qs = Course.objects.filter(
                        models.Q(id__in=allowed_course_ids) | models.Q(category_id__in=allowed_cat_ids)
                    ).distinct()
                else:
                    qs = Course.objects.none()
            elif user_role in ('teacher', 'faculty', 'educator', 'instructor'):
                inst = get_user_institution(user)
                assigned_qs = Course.objects.filter(created_by=user)
                if inst:
                    allowed_course_ids = set(inst.allowed_courses.values_list('id', flat=True))
                    allowed_cat_ids = set(inst.allowed_categories.values_list('id', flat=True))
                    inst_qs = Course.objects.filter(
                        models.Q(id__in=allowed_course_ids) | models.Q(category_id__in=allowed_cat_ids)
                    )
                    qs = (inst_qs | assigned_qs).distinct()
                else:
                    qs = assigned_qs.distinct()
            elif user_role == 'student' or hasattr(user, 'student_profile'):
                from courses.models import Enrollment
                enrolled_ids = set(Enrollment.objects.filter(student=user).values_list('course_id', flat=True))
                if enrolled_ids:
                    qs = Course.objects.filter(id__in=enrolled_ids, status='published').distinct()
                else:
                    qs = Course.objects.none()
            else:
                qs = Course.objects.none()
        else:
            qs = Course.objects.filter(status='published')

    books_q = models.Q(category__slug='ai-books') | models.Q(category__name__icontains='AI Book') | models.Q(title__icontains='AI-GUIDE') | models.Q(title__icontains='AI Book')
    if only_books:
        return qs.filter(books_q)
    elif exclude_books:
        return qs.exclude(books_q)
    return qs


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
