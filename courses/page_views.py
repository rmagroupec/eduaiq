"""
Template view for the public AI Books page.
Lives in the `frontend` app on purpose — this is the app your root urls.py
already dedicates to HTML template pages (included with no prefix at ''),
while `courses.urls` is API-only and prefixed with 'courses/'.

Books here are just Course objects filed under the "AI Books" category —
no separate Book model needed.

Add this file as frontend/page_views.py (or paste the function straight
into frontend/views.py if you'd rather keep one file).
"""

from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from courses.models import Course

AI_BOOKS_CATEGORY_SLUG = "ai-books"  # create this CourseCategory once in /admin/


def ai_books_page(request):
    now = timezone.now()

    base_qs = (
        Course.objects.filter(category__slug=AI_BOOKS_CATEGORY_SLUG)
        .select_related("category")
        .annotate(student_count=Count("enrollments", distinct=True))
    )

    # Live = published AND publish date has passed
    featured_books = base_qs.filter(
        status="published",
        published_at__lte=now,
    ).order_by("-student_count")[:3]

    # Coming soon = approved (ready, not yet published) OR published with a future date
    coming_soon_books = base_qs.filter(
        Q(status="approved") | Q(status="published", published_at__gt=now)
    ).order_by("-created_at")

    context = {
        "featured_books": featured_books,
        "coming_soon_books": coming_soon_books,
    }
    return render(request, "ai_books.html", context)