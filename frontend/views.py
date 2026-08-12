import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q

from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from courses.models import Course, CourseCategory, Quiz, QuizAttempt, Enrollment
from courses.utils import (
    get_allowed_courses_for_user,
    get_allowed_categories_for_user,
    is_course_accessible_by_user,
)
from olympiad.models import (
    OlympiadCategory,
    Olympiad,
    OlympiadQuiz,
    OlympiadQuestion,
    OlympiadRegistration,
    OlympiadAttempt,
    OlympiadResult,
)

User = get_user_model()

AI_BOOKS_CATEGORY_SLUG = "ai-books"  # create this CourseCategory once in /admin/


# ==========================
# Error Pages
# ==========================

def handler404(request, exception=None):
    """Custom 404 Page"""
    return render(request, "404page.html", status=404)


def handler500(request):
    """Custom 500 Page"""
    return render(request, "500page.html", status=500)


# ==========================
# Website Views (Public)
# ==========================

def home(request):
    """Homepage - Featured categories and courses for public & authenticated users"""
    categories = get_allowed_categories_for_user(request.user)
    return render(request, "index.html", {'categories': categories})


def about(request):
    """About page"""
    return render(request, "about.html")


def courses(request):
    """
    All courses listing page.
    Publicly accessible catalog display (excludes AI Books so books stay in AI Books section).
    """
    allowed_courses = get_allowed_courses_for_user(request.user, exclude_books=True)
    return render(request, "courses.html", {
        'courses': allowed_courses
    })


def course_detail(request):
    """
    Single course detail page with modules, lessons, and quizzes.
    Publicly viewable course overview, with content locks for unauthenticated or unallowed users.
    """
    course_slug = request.GET.get('slug', '')
    course = Course.objects.filter(slug=course_slug, status='published').first()

    if not course and not request.user.is_superuser:
        return render(request, "404page.html", status=404)

    is_accessible = is_course_accessible_by_user(request.user, course)

    return render(request, "course-detail.html", {
        'course_slug': course_slug,
        'course': course,
        'is_accessible': is_accessible,
    })


def categories(request):
    """
    Course categories listing.
    Publicly accessible catalog display.
    """
    categories_qs = get_allowed_categories_for_user(request.user)
    return render(request, "categories.html", {'categories': categories_qs})


def search(request):
    """
    Search results page.
    Publicly accessible.
    """
    query = request.GET.get('q', '')
    return render(request, "search.html", {
        'query': query
    })


def contact(request):
    """Contact page"""
    return render(request, "contact.html")


def faq(request):
    """FAQ page"""
    return render(request, "faq.html")


# ==========================
# Feature Pages
# ==========================

def skill_development(request):
    """Skill development courses"""
    return render(request, "skill-development.html")


def ai_lab(request):
    """AI Lab page"""
    return render(request, "ai-lab.html")


def ai_books(request):
    """
    AI Books page — books are Course objects filed under the "AI Books &
    Guides" category. Splits them into featured_books (live: published AND
    the publish date has passed or null) and coming_soon_books (approved, or
    published with a future date).
    """
    now = timezone.now()

    base_qs = (
        Course.objects.filter(category__slug=AI_BOOKS_CATEGORY_SLUG)
        .select_related("category")
        .annotate(student_count=Count("enrollments", distinct=True))
    )

    featured_books = base_qs.filter(
        Q(status="published") | Q(status="approved")
    ).order_by("-student_count", "-created_at")

    coming_soon_books = base_qs.filter(
        status="in_review"
    ).order_by("-created_at")

    return render(request, "ai-books.html", {
        'featured_books': featured_books,
        'coming_soon_books': coming_soon_books,
    })


def book_reader(request, slug):
    """
    Google Books style interactive reader view.
    Checks if the user has access to read the book via:
    1. Superuser / Staff / Admin role.
    2. Student enrolled in the book/course.
    3. Student belonging to an Institution assigned to the book.
    4. Free preview / public demo.
    """
    book = get_object_or_404(
        Course.objects.prefetch_related('modules__lessons'),
        slug=slug
    )

    user = request.user
    is_accessible = False

    if user.is_authenticated:
        if is_course_accessible_by_user(user, book):
            is_accessible = True
        elif Enrollment.objects.filter(student=user, course=book).exists():
            is_accessible = True

    # If book has price <= 0, allow reading access
    if not is_accessible and (not book.price or book.price <= 0):
        is_accessible = True

    return render(request, "book-reader.html", {
        'book': book,
        'is_accessible': is_accessible,
    })


def olympiads(request):
    """Olympiad competitions"""
    return render(request, "olympiads.html")


def career(request):
    """Career page"""
    return render(request, "career.html")


def team(request):
    """Team page"""
    return render(request, "team.html")


def gallery(request):
    """Gallery page"""
    return render(request, "gallery.html")


def testimonial(request):
    """Testimonial page"""
    return render(request, "testimonial.html")


def facility(request):
    """Facility page"""
    return render(request, "facility.html")


def growth_partner_kit(request):
    """Growth Partner Kit page"""
    return render(request, "growth-partner-kit.html")


def apply_for_franchise(request):
    """Apply for Franchise page"""
    return render(request, "apply-for-franchise.html")


def eduaiq_ecosystem(request):
    """EduAiQ Ecosystem page"""
    return render(request, "eduaiq-ecosystem.html")


# ==========================
# Learning Pages (Login Required)
# ==========================

@login_required(login_url='/login/')
def my_learning(request):
    """
    Student learning dashboard - shows institution-assigned courses, AI Books,
    quizzes/assessments, Olympiad Entrance Exams, Certificates, Student ID Card, and Admit Cards.
    Template: my-learning.html
    """
    entrance_registrations = list(OlympiadRegistration.objects.filter(
        student=request.user
    ).select_related('olympiad').order_by('-registered_at'))

    completed_count = 0
    in_progress_count = 0
    not_started_count = 0

    certificates_list = []
    admit_cards_list = []

    for reg in entrance_registrations:
        attempt = OlympiadAttempt.objects.filter(registration=reg).first()
        reg.active_attempt = attempt
        
        # Admit card payload
        admit_cards_list.append({
            'exam_name': reg.olympiad.name,
            'roll_number': reg.roll_number,
            'registered_at': reg.registered_at,
            'class_group': reg.olympiad.class_group,
            'duration_minutes': reg.olympiad.exam_duration_minutes,
            'exam_id': reg.olympiad.id,
            'is_completed': bool(attempt and attempt.submitted_at),
        })

        if not attempt:
            reg.status_label = 'Not Started'
            reg.status_badge_class = 'bg-secondary text-white'
            reg.action_label = 'Start Entrance Exam'
            reg.is_completed = False
            not_started_count += 1
        elif not attempt.submitted_at:
            reg.status_label = 'In Progress'
            reg.status_badge_class = 'bg-warning text-dark'
            reg.action_label = 'Resume Exam'
            reg.is_completed = False
            in_progress_count += 1
        else:
            reg.status_label = 'Completed'
            reg.status_badge_class = 'bg-success text-white'
            reg.action_label = 'View Result / Status'
            reg.is_completed = True
            completed_count += 1
            
            # Certificate payload
            pct = float(attempt.score_pct or 0)
            if pct >= 85.0:
                award = "Gold Medal & 100% Scholarship"
            elif pct >= 70.0:
                award = "Silver Medal & 50% Scholarship"
            elif pct >= 50.0:
                award = "Bronze Medal & 25% Scholarship"
            else:
                award = "Certificate of Participation"
                
            certificates_list.append({
                'title': f"{reg.olympiad.name} - Merit Certificate",
                'type': 'Olympiad Entrance',
                'issued_date': attempt.submitted_at,
                'cert_url': f"/olympiad-entrance/{reg.olympiad.id}/certificate/",
                'serial_no': f"EDUAIQ-CERT-{reg.olympiad.id}-{reg.roll_number}",
                'award': award,
                'score_pct': attempt.score_pct,
            })

    # Student ID Card Data
    from institutions.models import Student
    student_profile = Student.objects.filter(user=request.user).select_related('institution').first()
    inst_name = student_profile.institution.name if (student_profile and student_profile.institution) else "EduAiQ Academy"
    roll_no = student_profile.roll_number if (student_profile and student_profile.roll_number) else f"STU-{request.user.id:05d}"
    
    id_card_data = {
        'full_name': request.user.get_full_name() or request.user.username,
        'username': request.user.username,
        'email': request.user.email,
        'phone': getattr(request.user, 'phone', '') or 'N/A',
        'role': getattr(request.user, 'role', 'student').capitalize(),
        'roll_number': roll_no,
        'institution_name': inst_name,
        'joined_date': request.user.date_joined,
    }

    # ---------------------------------------------------------
    # Institution Allotted Courses & AI Books
    # ---------------------------------------------------------
    allowed_courses_qs = get_allowed_courses_for_user(request.user, exclude_books=False)
    
    assigned_courses = list(allowed_courses_qs.exclude(category__slug=AI_BOOKS_CATEGORY_SLUG).select_related('category'))
    assigned_books = list(allowed_courses_qs.filter(category__slug=AI_BOOKS_CATEGORY_SLUG).select_related('category'))

    direct_enrollments = list(Enrollment.objects.filter(student=request.user).select_related('course', 'course__category'))
    enrollment_map = {e.course_id: e for e in direct_enrollments}
    
    for e in direct_enrollments:
        c = e.course
        if c.category and c.category.slug == AI_BOOKS_CATEGORY_SLUG:
            if c not in assigned_books:
                assigned_books.append(c)
        else:
            if c not in assigned_courses:
                assigned_courses.append(c)

    assigned_courses_data = []
    total_progress_sum = 0.0
    for c in assigned_courses:
        e = enrollment_map.get(c.id)
        pct = float(e.progress_pct) if e else 0.0
        total_progress_sum += pct
        is_comp = e.is_completed if e else False
        assigned_courses_data.append({
            'course': c,
            'progress_pct': pct,
            'is_completed': is_comp,
        })

    avg_progress = round(total_progress_sum / len(assigned_courses)) if assigned_courses else 0

    assigned_books_data = []
    for b in assigned_books:
        assigned_books_data.append({
            'book': b,
            'is_accessible': True,
        })

    # ---------------------------------------------------------
    # Institution Assigned Quizzes & Assessments
    # ---------------------------------------------------------
    all_assigned_course_ids = [c.id for c in assigned_courses] + [b.id for b in assigned_books]
    quizzes_qs = Quiz.objects.filter(
        lesson__module__course_id__in=all_assigned_course_ids,
        is_active=True
    ).select_related('lesson', 'lesson__module', 'lesson__module__course')

    assigned_quizzes_data = []
    completed_quizzes_count = 0
    for quiz in quizzes_qs:
        attempt = QuizAttempt.objects.filter(quiz=quiz, student=request.user).order_by('-started_at').first()
        status_label = 'Not Started'
        badge_class = 'bg-secondary text-white'
        if attempt:
            if attempt.status in ('submitted', 'graded') or attempt.submitted_at:
                status_label = 'Completed'
                badge_class = 'bg-success text-white'
                completed_quizzes_count += 1
            else:
                status_label = 'In Progress'
                badge_class = 'bg-warning text-dark'
        
        assigned_quizzes_data.append({
            'quiz': quiz,
            'course_title': quiz.lesson.module.course.title if (quiz.lesson and quiz.lesson.module) else 'General Course',
            'lesson_title': quiz.lesson.title if quiz.lesson else 'Assessment Quiz',
            'latest_attempt': attempt,
            'status_label': status_label,
            'badge_class': badge_class,
            'passing_score': quiz.passing_score_pct,
            'time_limit': quiz.time_limit_minutes,
        })

    return render(request, "my-learning.html", {
        'entrance_registrations': entrance_registrations,
        'total_entrance_count': len(entrance_registrations),
        'completed_entrance_count': completed_count,
        'in_progress_entrance_count': in_progress_count,
        'not_started_entrance_count': not_started_count,
        'id_card': id_card_data,
        'certificates_list': certificates_list,
        'admit_cards_list': admit_cards_list,
        'assigned_courses_data': assigned_courses_data,
        'assigned_books_data': assigned_books_data,
        'assigned_quizzes_data': assigned_quizzes_data,
        'total_assigned_courses': len(assigned_courses_data),
        'total_assigned_books': len(assigned_books_data),
        'total_assigned_quizzes': len(assigned_quizzes_data),
        'completed_quizzes_count': completed_quizzes_count,
        'avg_progress': avg_progress,
    })



@login_required(login_url='/admin-panel/login/')
def quiz_player(request):
    """
    Quiz taking interface with timer and encrypted questions
    Template: quiz-player.html
    APIs:
      - POST /quizzes/{id}/start/
      - POST /attempts/{id}/answer/
      - POST /attempts/{id}/submit/
    Query Params: id (quiz ID)
    Requires: User authentication
    """
    quiz_id = request.GET.get('id', '')
    return render(request, "quiz-player.html", {
        'quiz_id': quiz_id
    })


@login_required(login_url='/admin-panel/login/')
def lesson_player(request):
    """
    Lesson viewing interface with video/text/pdf support
    Template: lesson-player.html
    APIs:
      - GET /courses/lessons/{id}/
      - PATCH /courses/enrollments/{id}/progress/
    Query Params: id (lesson ID)
    Requires: User authentication
    """
    lesson_id = request.GET.get('id', '')
    return render(request, "lesson-player.html", {
        'lesson_id': lesson_id
    })


# ==========================
# Admin Panel Views
# ==========================

@login_required(login_url='/admin-panel/login/')
def dashboard(request):
    """
    Real-World Admin Dashboard - Computes live counts and recent records across platform entities.
    """
    total_students = User.objects.filter(role='student').count() or User.objects.count()
    try:
        from institutions.models import Institution
        total_institutions = Institution.objects.count()
        recent_institutions = Institution.objects.order_by('-created_at')[:5]
    except Exception:
        total_institutions = 0
        recent_institutions = []

    total_courses = Course.objects.count()
    recent_courses = Course.objects.order_by('-created_at')[:5] if total_courses else []
    total_teachers = User.objects.filter(role='teacher').count()
    total_olympiads = Olympiad.objects.filter(is_active=True).count()
    total_registrations = OlympiadRegistration.objects.count()
    total_attempts = OlympiadAttempt.objects.count()
    recent_registrations = OlympiadRegistration.objects.select_related('olympiad', 'student').order_by('-registered_at')[:5]

    return render(request, "admin_panel/index.html", {
        'total_students': total_students,
        'total_institutions': total_institutions,
        'recent_institutions': recent_institutions,
        'total_courses': total_courses,
        'recent_courses': recent_courses,
        'total_teachers': total_teachers,
        'total_olympiads': total_olympiads,
        'total_registrations': total_registrations,
        'total_attempts': total_attempts,
        'recent_registrations': recent_registrations,
    })




@login_required(login_url='/admin-panel/login/')
def users(request):
    """Admin users management - Superadmin Only"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return redirect('admin_panel')
    return render(request, "admin_panel/users.html")


@login_required(login_url='/admin-panel/login/')
def admin_profile(request):
    """Admin profile details page"""
    return render(request, "admin_panel/view-profile.html")


@login_required(login_url='/admin-panel/login/')
def admin_courses(request):
    """Admin course list page"""
    return render(request, "admin_panel/course-list.html")


@login_required(login_url='/admin-panel/login/')
def admin_add_course(request):
    """Admin add new course page"""
    return render(request, "admin_panel/add-new-course.html")


@login_required(login_url='/admin-panel/login/')
def admin_edit_course(request):
    """Admin edit course page"""
    return render(request, "admin_panel/edit-course.html")


@login_required(login_url='/admin-panel/login/')
def admin_course_details(request):
    """Admin course details page"""
    return render(request, "admin_panel/course-details.html")


@login_required(login_url='/admin-panel/login/')
def admin_books(request):
    """
    Admin AI Books list page. All data (title, status, is_live/is_coming_soon,
    etc.) is fetched client-side from /courses/courses/?category=ai-books —
    same pattern as admin_courses + course-list.html.
    """
    return render(request, "admin_panel/books-list.html")


@login_required(login_url='/admin-panel/login/')
def admin_add_book(request):
    """Admin add new AI Book page — POSTs to /courses/courses/ with category locked to ai-books."""
    return render(request, "admin_panel/add-book.html")


@login_required(login_url='/admin-panel/login/')
def admin_page_router(request, page_name):
    """
    Dynamic router for admin panel views with Role-Based Access Control (RBAC).
    Maps /admin-panel/<page_name>/ to template: admin_panel/<page_name>.html
    """
    from django.template.loader import get_template
    from django.template import TemplateDoesNotExist

    # Superadmin-only pages restricted for Institution Admins
    superadmin_only_pages = [
        'users', 'add-new-institution', 'institution-list', 'edit-institution',
        'categories', 'role-permission', 'assign-role', 'general', 'company',
        'notification-alert', 'payment-gateway', 'currencies', 'languages'
    ]

    if request.user.role == 'institution' and page_name in superadmin_only_pages:
        return redirect('admin_panel')

    mapping = {
        'courses': 'admin_panel/course-list.html',
        'view-profile': 'admin_panel/view-profile.html',
        'profile': 'admin_panel/view-profile.html',
    }

    if page_name in mapping:
        return render(request, mapping[page_name])

    possible_templates = [
        f"admin_panel/{page_name}.html",
        f"admin_panel/{page_name}-list.html",
    ]

    for t in possible_templates:
        try:
            get_template(t)
            return render(request, t)
        except TemplateDoesNotExist:
            continue

    return render(request, "admin_panel/index.html")


# ==========================
# Blog & Content Pages
# ==========================

def blog_archive(request):
    """Blog archive"""
    return render(request, "blog-archive.html")


def single_blog(request):
    """Single blog post"""
    return render(request, "single-blog.html")


def product_archive(request):
    """Product/Course archive"""
    return render(request, "product-archive.html")


def product_detail(request):
    """Single product detail"""
    return render(request, "product-detail.html")


def product_cart(request):
    """Shopping cart"""
    return render(request, "product-cart.html")


def product_checkout(request):
    """Checkout page"""
    return render(request, "product-checkout.html")


def career_detail(request):
    """Single career opportunity"""
    return render(request, "career-detail.html")


def team_detail(request):
    """Single team member"""
    return render(request, "team-detail.html")


def single_page(request, slug):
    """Single page (generic)"""
    if slug == 'support':
        return render(request, "support.html")
    return render(request, "single-page.html")


def coming_soon(request):
    """Coming soon page"""
    return render(request, "comming-soon.html")


def legal_notice(request):
    """Legal notice page"""
    return render(request, "legal-notice.html")


# ==========================
# Olympiad Pages
# ==========================

def olympiad_curriculum(request):
    """Olympiad curriculum"""
    return render(request, "olympiad-curriculum.html")


def olympiad_form(request):
    """Olympiad registration form"""
    return render(request, "olympiad-form.html")


# ==========================
# Auth Views
# ==========================

def _get_redirect_url_for_user(request, user):
    """Determine smart redirect target after login based on next parameter or user role."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return next_url

    if getattr(user, 'role', '') == 'student':
        return '/my-learning/'
    elif getattr(user, 'role', '') in ['institution', 'admin', 'partner'] or user.is_staff or user.is_superuser:
        return '/admin-panel/dashboard/'
    
    return '/my-learning/'


def login_view(request):
    """
    GET  -> login form dikhata hai
    POST -> username YA email dono se login allow karta hai
    """
    next_param = request.GET.get('next', '')
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        username_to_try = identifier

        # Agar user ne email daala hai, uske corresponding username nikal lo
        if '@' in identifier:
            matched_user = User.objects.filter(email__iexact=identifier).first()
            if matched_user:
                username_to_try = matched_user.username

        user = authenticate(request, username=username_to_try, password=password)

        if user is not None:
            login(request, user)
            return redirect(_get_redirect_url_for_user(request, user))

        return render(request, 'admin_panel/login.html', {
            'form_errors': ["Invalid username or password."],
            'old_username': identifier,
            'next': next_param,
        })

    return render(request, 'admin_panel/login.html', {'next': next_param})


def institution_login_view(request):
    """
    Institution Partner & Admin Login View.
    GET  -> Renders institution_login.html form
    POST -> Authenticates institution admin/partner and redirects to Admin Panel Dashboard
    """
    next_param = request.GET.get('next', '')
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        username_to_try = identifier

        if '@' in identifier:
            matched_user = User.objects.filter(email__iexact=identifier).first()
            if matched_user:
                username_to_try = matched_user.username

        user = authenticate(request, username=username_to_try, password=password)

        if user is not None:
            login(request, user)
            return redirect(_get_redirect_url_for_user(request, user))

        return render(request, 'institution_login.html', {
            'form_errors': ["Invalid Institution Credentials or Password."],
            'old_username': identifier,
            'next': next_param,
        })

    return render(request, 'institution_login.html', {'next': next_param})



def register_view(request):
    form_errors = []

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            form_errors.append('Username already taken')
        else:
            User.objects.create_user(username=username, email=email, password=password)
            return redirect('login')

    return render(request, 'admin_panel/register.html', {
        'form_errors': form_errors,
    })

def register_submit(request):
    """
    register.html isi view par POST karta hai. Success pe login page pe redirect.
    """
    if request.method != 'POST':
        return redirect('register')

    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    role = request.POST.get('role', '').strip()

    errors = []

    if not username or not email or not phone or not password1 or not password2 or not role:
        errors.append("Please fill all required fields.")

    if password1 != password2:
        errors.append("Passwords do not match.")

    if password1 and len(password1) < 8:
        errors.append("Password must be at least 8 characters long.")

    if username and User.objects.filter(username=username).exists():
        errors.append("This username is already taken.")

    if phone and User.objects.filter(phone=phone).exists():
        errors.append("This phone number is already registered.")

    if email and User.objects.filter(email=email).exists():
        errors.append("This email is already registered.")

    if errors:
        return render(request, 'admin_panel/register.html', {
            'form_errors': errors,
            'old_username': username,
            'old_email': email,
            'old_phone': phone,
            'old_role': role,
        })

    user = User(username=username, email=email, phone=phone, role=role)
    user.set_password(password1)
    user.save()

    return redirect('login')   # ✅ register -> login page


def logout_view(request):
    logout(request)
    return redirect('/courses/')


# ==========================
# API Integration Helper Views
# ==========================

@login_required(login_url='/admin-panel/login/')
def course_progress(request):
    """
    Update course progress
    Template: my-learning.html (embedded)
    API: PATCH /courses/enrollments/{id}/progress/
    Requires: User authentication
    """
    return render(request, "my-learning.html")


# ==========================
# Olympiad Entrance Exam Views
# ==========================

def olympiad_entrance_list(request):
    """Catalog listing all Olympiad Entrance Exams"""
    entrance_cat = OlympiadCategory.objects.filter(name__icontains='Olympiad Entrance').first()
    if entrance_cat:
        exams = Olympiad.objects.filter(category=entrance_cat, is_active=True)
    else:
        exams = Olympiad.objects.filter(is_active=True)

    registered_exam_ids = []
    if request.user.is_authenticated:
        registered_exam_ids = list(
            OlympiadRegistration.objects.filter(student=request.user).values_list('olympiad_id', flat=True)
        )

    return render(request, "olympiad-entrance-list.html", {
        'exams': exams,
        'entrance_cat': entrance_cat,
        'registered_exam_ids': registered_exam_ids,
    })


def olympiad_entrance_detail(request, pk):
    """Detail view for a single Olympiad Entrance Exam"""
    exam = get_object_or_404(Olympiad, pk=pk, is_active=True)
    registration = None
    if request.user.is_authenticated:
        registration = OlympiadRegistration.objects.filter(olympiad=exam, student=request.user).first()

    assigned_quizzes = exam.olympiad_quizzes.select_related('quiz', 'quiz__lesson').all()
    direct_questions_count = exam.questions.count()

    total_questions = direct_questions_count
    for oq in assigned_quizzes:
        total_questions += oq.quiz.questions.filter(is_active=True).count()

    return render(request, "olympiad-entrance-detail.html", {
        'exam': exam,
        'registration': registration,
        'assigned_quizzes': assigned_quizzes,
        'direct_questions_count': direct_questions_count,
        'total_questions': total_questions,
    })


@login_required(login_url='/login/')
def olympiad_entrance_enroll(request, pk):
    """Handle student enrollment / registration for an entrance exam"""
    exam = get_object_or_404(Olympiad, pk=pk, is_active=True)
    
    registration, created = OlympiadRegistration.objects.get_or_create(
        olympiad=exam,
        student=request.user,
        defaults={
            'roll_number': f"ENT-{exam.id}-{request.user.id}-{int(timezone.now().timestamp()) % 10000}",
            'status': 'registered',
        }
    )
    if created:
        messages.success(request, f"Successfully enrolled in {exam.name}! Your Roll Number is {registration.roll_number}.")
    else:
        messages.info(request, f"You are already enrolled in {exam.name}. Roll Number: {registration.roll_number}.")
    
    return redirect('olympiad_entrance_detail', pk=pk)


@login_required(login_url='/login/')
def olympiad_entrance_attempt(request, pk):
    """
    Distraction-free exam player interface for taking the Olympiad Entrance Exam.
    Combines direct OlympiadQuestions and assigned Quiz questions.
    Enforces Strict Access Control: Only enrolled students can access!
    """
    exam = get_object_or_404(Olympiad, pk=pk, is_active=True)
    registration = OlympiadRegistration.objects.filter(olympiad=exam, student=request.user).first()

    # Strict Access Guard: Block non-enrolled students
    if not registration:
        messages.error(request, "Please enroll in the Olympiad Entrance course to access this exam.")
        return redirect('olympiad_entrance_detail', pk=pk)


    # Check if student already submitted attempt
    attempt = OlympiadAttempt.objects.filter(registration=registration).first()
    if attempt and attempt.submitted_at:
        return redirect('olympiad_entrance_result', pk=pk)

    if not attempt:
        attempt = OlympiadAttempt.objects.create(
            registration=registration,
            started_at=timezone.now(),
        )
    elif not attempt.started_at:
        attempt.started_at = timezone.now()
        attempt.save()


    sections = []

    # 1. Direct Olympiad Questions section
    direct_qs = list(exam.questions.all())
    if direct_qs:
        sec_questions = []
        for q in direct_qs:
            sec_questions.append({
                'id': f"direct_{q.id}",
                'raw_id': q.id,
                'source': 'direct',
                'question_type': q.question_type,
                'question_text': q.question_text,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
                'marks': q.marks,
            })
        sections.append({
            'name': 'Section 1: General Entrance Questions',
            'questions': sec_questions,
        })

    # 2. Assigned Quizzes sections
    assigned_quizzes = exam.olympiad_quizzes.select_related('quiz', 'quiz__lesson').all()
    for idx, oq in enumerate(assigned_quizzes, start=len(sections) + 1):
        quiz_questions = oq.quiz.questions.filter(is_active=True)
        sec_questions = []
        for q in quiz_questions:
            opts = q.get_options()
            sec_questions.append({
                'id': f"quiz_{q.id}",
                'raw_id': q.id,
                'source': 'quiz',
                'question_type': 'mcq',
                'question_text': q.question_text,
                'option_a': opts.get('a', ''),
                'option_b': opts.get('b', ''),
                'option_c': opts.get('c', ''),
                'option_d': opts.get('d', ''),
                'marks': q.marks,
            })
        if sec_questions:
            sections.append({
                'name': oq.section_name or f"Section {idx}: {oq.quiz.lesson.title}",
                'questions': sec_questions,
            })

    existing_responses = {}
    if attempt.responses_json:
        try:
            existing_responses = json.loads(attempt.responses_json)
        except Exception:
            existing_responses = {}

    return render(request, "olympiad-entrance-player.html", {
        'exam': exam,
        'registration': registration,
        'attempt': attempt,
        'sections_json': json.dumps(sections),
        'existing_responses_json': json.dumps(existing_responses),
        'duration_minutes': exam.exam_duration_minutes,
    })


@login_required(login_url='/login/')
def olympiad_entrance_submit(request, pk):
    """
    Handle POST submission of answers for Olympiad Entrance Exam.
    Auto-grades answers and records attempt results.
    """
    if request.method != 'POST':
        return redirect('olympiad_entrance_detail', pk=pk)

    exam = get_object_or_404(Olympiad, pk=pk)
    registration = get_object_or_404(OlympiadRegistration, olympiad=exam, student=request.user)
    attempt, _ = OlympiadAttempt.objects.get_or_create(registration=registration)

    payload = request.POST.get('responses', '{}')
    try:
        submitted_responses = json.loads(payload)
    except Exception:
        submitted_responses = {}

    total_marks = 0
    obtained_marks = 0

    # Grade direct questions
    for q in exam.questions.all():
        total_marks += q.marks
        user_ans = str(submitted_responses.get(f"direct_{q.id}", "")).strip().lower()
        correct_ans = str(q.correct_option).strip().lower()

        if q.question_type == 'mcq':
            if user_ans == correct_ans:
                obtained_marks += q.marks
        elif q.question_type == 'true_false':
            if user_ans == correct_ans:
                obtained_marks += q.marks
        elif q.question_type == 'multi_select':
            user_set = set([x.strip() for x in user_ans.split(',') if x.strip()])
            correct_set = set([x.strip() for x in correct_ans.split(',') if x.strip()])
            if user_set and user_set == correct_set:
                obtained_marks += q.marks
        elif q.question_type == 'numerical':
            try:
                if float(user_ans) == float(correct_ans):
                    obtained_marks += q.marks
            except ValueError:
                if user_ans == correct_ans:
                    obtained_marks += q.marks

    # Grade assigned quiz questions
    assigned_quizzes = exam.olympiad_quizzes.select_related('quiz').all()
    for oq in assigned_quizzes:
        for q in oq.quiz.questions.filter(is_active=True):
            total_marks += q.marks
            user_ans = str(submitted_responses.get(f"quiz_{q.id}", "")).strip().lower()
            correct_ans = str(q.correct_option or '').strip().lower()
            if user_ans and user_ans == correct_ans:
                obtained_marks += q.marks

    score_pct = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
    passed = score_pct >= 40.0

    attempt.raw_score = obtained_marks
    attempt.total_marks = total_marks
    attempt.score_pct = score_pct
    attempt.passed = passed
    attempt.responses_json = json.dumps(submitted_responses)
    attempt.submitted_at = timezone.now()
    attempt.save()

    return redirect('olympiad_entrance_result', pk=pk)


@login_required(login_url='/login/')
def olympiad_entrance_result(request, pk):
    """
    Result page for Olympiad Entrance Exam.
    Enforces configurable result timing:
    - instant / immediate: Instant Result
    - after_2_hours: 2 hours after submission
    - next_day: Following day at configured release time
    - scheduled: Fixed date/time
    - manual: Explicit admin publishing
    """
    exam = get_object_or_404(Olympiad, pk=pk)
    registration = get_object_or_404(OlympiadRegistration, olympiad=exam, student=request.user)
    attempt = get_object_or_404(OlympiadAttempt, registration=registration)

    now = timezone.now()
    is_published = False
    unlock_time = None

    if exam.result_display_mode == 'immediate':
        is_published = True
    elif exam.result_display_mode == 'after_2_hours':
        if attempt.submitted_at:
            unlock_time = attempt.submitted_at + timedelta(hours=2)
            if now >= unlock_time:
                is_published = True
    elif exam.result_display_mode == 'next_day':
        if attempt.submitted_at:
            submitted_date = attempt.submitted_at.date()
            next_day_date = submitted_date + timedelta(days=1)
            release_time = exam.next_day_release_time or datetime.strptime("09:00:00", "%H:%M:%S").time()
            naive_unlock = datetime.combine(next_day_date, release_time)
            if timezone.is_aware(attempt.submitted_at):
                unlock_time = timezone.make_aware(naive_unlock, timezone.get_current_timezone())
            else:
                unlock_time = naive_unlock

            if now >= unlock_time:
                is_published = True
    elif exam.result_display_mode == 'scheduled':
        if exam.result_declaration_date:
            unlock_time = exam.result_declaration_date
            if now >= unlock_time:
                is_published = True
    elif exam.result_display_mode == 'manual':
        if hasattr(registration, 'result') and registration.result is not None:
            is_published = True

    # Award & Medal Tier logic
    pct = float(attempt.score_pct or 0)
    if pct >= 85.0:
        award_title = "Gold Medal & 100% Scholarship Band"
        medal_badge = "🥇 Gold Medalist"
        medal_class = "badge bg-warning text-dark fs-6"
    elif pct >= 70.0:
        award_title = "Silver Medal & 50% Scholarship Band"
        medal_badge = "🥈 Silver Medalist"
        medal_class = "badge bg-secondary text-white fs-6"
    elif pct >= 50.0:
        award_title = "Bronze Medal & 25% Scholarship Band"
        medal_badge = "🥉 Bronze Medalist"
        medal_class = "badge bg-dark text-white fs-6"
    else:
        award_title = "Certificate of Participation"
        medal_badge = "📜 Participant"
        medal_class = "badge bg-info text-dark fs-6"

    # Detailed Question Review Breakdown
    review_questions = []
    submitted_responses = {}
    if attempt.responses_json:
        try:
            submitted_responses = json.loads(attempt.responses_json)
        except Exception:
            submitted_responses = {}

    # Direct Questions
    for q in exam.questions.all():
        u_ans = str(submitted_responses.get(f"direct_{q.id}", "")).strip().lower()
        c_ans = str(q.correct_option or "").strip().lower()
        is_corr = (u_ans == c_ans) if u_ans else False
        review_questions.append({
            'text': q.question_text,
            'user_ans': u_ans.upper() if u_ans else 'Not Attempted',
            'correct_ans': c_ans.upper(),
            'is_correct': is_corr,
            'explanation': q.explanation or 'No detailed solution required for this standard question.',
            'marks': q.marks,
        })

    # Assigned Quiz Questions
    for oq in exam.olympiad_quizzes.select_related('quiz').all():
        for q in oq.quiz.questions.filter(is_active=True):
            u_ans = str(submitted_responses.get(f"quiz_{q.id}", "")).strip().lower()
            c_ans = str(q.correct_option or "").strip().lower()
            is_corr = (u_ans == c_ans) if u_ans else False
            review_questions.append({
                'text': q.question_text,
                'user_ans': u_ans.upper() if u_ans else 'Not Attempted',
                'correct_ans': c_ans.upper(),
                'is_correct': is_corr,
                'explanation': getattr(q, 'explanation', 'Standard choice question.'),
                'marks': q.marks,
            })

    return render(request, "olympiad-entrance-result.html", {
        'exam': exam,
        'registration': registration,
        'attempt': attempt,
        'is_published': is_published,
        'unlock_time': unlock_time,
        'now': now,
        'award_title': award_title,
        'medal_badge': medal_badge,
        'medal_class': medal_class,
        'review_questions': review_questions,
    })


@login_required(login_url='/login/')
def olympiad_entrance_certificate(request, pk):
    """
    Renders official printable Merit / Participation Certificate for student.
    """
    exam = get_object_or_404(Olympiad, pk=pk)
    registration = get_object_or_404(OlympiadRegistration, olympiad=exam, student=request.user)
    attempt = get_object_or_404(OlympiadAttempt, registration=registration)

    pct = float(attempt.score_pct or 0)
    if pct >= 85.0:
        award_title = "Gold Medal & 100% Scholarship Band"
        cert_type = "Certificate of Gold Merit"
    elif pct >= 70.0:
        award_title = "Silver Medal & 50% Scholarship Band"
        cert_type = "Certificate of Silver Merit"
    elif pct >= 50.0:
        award_title = "Bronze Medal & 25% Scholarship Band"
        cert_type = "Certificate of Bronze Merit"
    else:
        award_title = "Certificate of Participation"
        cert_type = "Certificate of Participation"

    cert_serial = f"EDUAIQ-CERT-{exam.id}-{registration.roll_number}"

    return render(request, "olympiad-entrance-certificate.html", {
        'exam': exam,
        'registration': registration,
        'attempt': attempt,
        'award_title': award_title,
        'cert_type': cert_type,
        'cert_serial': cert_serial,
    })


# ==========================
# EduDash Admin Panel Views for Olympiad Entrance
# ==========================

@login_required(login_url='/admin-panel/login/')
def admin_olympiad_entrance_list(request):
    """
    EduDash Admin Management Page for Olympiad Entrance Exams.
    Template: admin_panel/olympiad-entrance-manage.html
    """
    exams = list(Olympiad.objects.filter(category__name='Olympiad Entrance').order_by('-id'))
    if not exams:
        exams = list(Olympiad.objects.all().order_by('-id'))

    for exam in exams:
        exam.enrolled_count = OlympiadRegistration.objects.filter(olympiad=exam).count()
        exam.attempt_count = OlympiadAttempt.objects.filter(registration__olympiad=exam).count()

    total_exams = len(exams)
    total_candidates = OlympiadRegistration.objects.count()
    total_attempts = OlympiadAttempt.objects.count()

    return render(request, "admin_panel/olympiad-entrance-manage.html", {
        'exams': exams,
        'total_exams': total_exams,
        'total_candidates': total_candidates,
        'total_attempts': total_attempts,
    })


@login_required(login_url='/admin-panel/login/')
def admin_olympiad_entrance_toggle(request, pk):
    """Toggle is_active status of an Olympiad Entrance Exam."""
    exam = get_object_or_404(Olympiad, pk=pk)
    exam.is_active = not exam.is_active
    exam.save()
    status_str = "activated" if exam.is_active else "disabled"
    messages.success(request, f"Exam '{exam.name}' was successfully {status_str}.")
    return redirect('admin_olympiad_entrance_list')


@login_required(login_url='/admin-panel/login/')
def admin_olympiad_entrance_add(request):
    """EduDash form to create a new Olympiad Entrance Exam."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        level = request.POST.get('level', 'school')
        class_group = request.POST.get('class_group', 'Class 6-10')
        exam_duration_minutes = int(request.POST.get('exam_duration_minutes', 45))
        result_display_mode = request.POST.get('result_display_mode', 'immediate')
        fee = float(request.POST.get('fee', 0))
        is_active = request.POST.get('is_active') == 'on'

        cat, _ = OlympiadCategory.objects.get_or_create(
            name='Olympiad Entrance',
            defaults={'description': 'Category for official Olympiad Entrance Examinations'}
        )

        exam = Olympiad.objects.create(
            category=cat,
            name=name,
            level=level,
            class_group=class_group,
            exam_duration_minutes=exam_duration_minutes,
            result_display_mode=result_display_mode,
            fee=fee,
            is_active=is_active,
            exam_date=timezone.now() + timedelta(days=7),
            registration_start=timezone.now(),
            registration_end=timezone.now() + timedelta(days=30),
        )
        messages.success(request, f"Olympiad Entrance Exam '{exam.name}' created successfully!")
        return redirect('admin_olympiad_entrance_list')

    return render(request, "admin_panel/add-olympiad-entrance.html", {
        'result_modes': Olympiad.RESULT_MODES,
    })


@login_required(login_url='/admin-panel/login/')
def admin_olympiad_entrance_edit(request, pk):
    """EduDash form to edit an existing Olympiad Entrance Exam."""
    exam = get_object_or_404(Olympiad, pk=pk)

    if request.method == 'POST':
        exam.name = request.POST.get('name', exam.name).strip()
        exam.level = request.POST.get('level', exam.level)
        exam.class_group = request.POST.get('class_group', exam.class_group)
        exam.exam_duration_minutes = int(request.POST.get('exam_duration_minutes', exam.exam_duration_minutes))
        exam.result_display_mode = request.POST.get('result_display_mode', exam.result_display_mode)
        exam.fee = float(request.POST.get('fee', exam.fee))
        exam.is_active = request.POST.get('is_active') == 'on'
        exam.save()

        messages.success(request, f"Exam '{exam.name}' details updated successfully!")
        return redirect('admin_olympiad_entrance_list')

    return render(request, "admin_panel/add-olympiad-entrance.html", {
        'exam': exam,
        'result_modes': Olympiad.RESULT_MODES,
    })


@login_required(login_url='/admin-panel/login/')
def admin_olympiad_entrance_questions(request, pk):
    """
    EduDash Admin page to add, view, and manage Questions & Quizzes for a specific Olympiad Entrance Exam.
    Template: admin_panel/manage-olympiad-questions.html
    """
    exam = get_object_or_404(Olympiad, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_question':
            q_text = request.POST.get('question_text', '').strip()
            q_type = request.POST.get('question_type', 'mcq')
            opt_a = request.POST.get('option_a', '').strip()
            opt_b = request.POST.get('option_b', '').strip()
            opt_c = request.POST.get('option_c', '').strip()
            opt_d = request.POST.get('option_d', '').strip()
            corr_opt = request.POST.get('correct_option', '').strip()
            expl = request.POST.get('explanation', '').strip()
            diff = request.POST.get('difficulty', 'medium')
            marks = int(request.POST.get('marks', 1))

            if q_text and corr_opt:
                OlympiadQuestion.objects.create(
                    olympiad=exam,
                    question_type=q_type,
                    question_text=q_text,
                    option_a=opt_a,
                    option_b=opt_b,
                    option_c=opt_c,
                    option_d=opt_d,
                    correct_option=corr_opt,
                    explanation=expl,
                    difficulty=diff,
                    marks=marks,
                )
                messages.success(request, "New question added successfully to exam!")
            else:
                messages.error(request, "Question text and Correct option are required.")

        elif action == 'delete_question':
            q_id = request.POST.get('question_id')
            if q_id:
                OlympiadQuestion.objects.filter(id=q_id, olympiad=exam).delete()
                messages.success(request, "Question deleted successfully.")

        elif action == 'assign_quiz':
            quiz_id = request.POST.get('quiz_id')
            sec_name = request.POST.get('section_name', '').strip()
            if quiz_id:
                quiz_obj = get_object_or_404(Quiz, id=quiz_id)
                OlympiadQuiz.objects.get_or_create(
                    olympiad=exam,
                    quiz=quiz_obj,
                    defaults={'section_name': sec_name}
                )
                messages.success(request, f"Quiz '{quiz_obj.lesson.title}' assigned to exam.")

        elif action == 'remove_quiz':
            oq_id = request.POST.get('olympiad_quiz_id')
            if oq_id:
                OlympiadQuiz.objects.filter(id=oq_id, olympiad=exam).delete()
                messages.success(request, "Assigned quiz removed from exam.")

        return redirect('admin_olympiad_entrance_questions', pk=pk)

    direct_questions = exam.questions.all().order_by('-id')
    assigned_quizzes = exam.olympiad_quizzes.select_related('quiz', 'quiz__lesson').all()
    available_quizzes = Quiz.objects.filter(is_active=True).exclude(
        id__in=assigned_quizzes.values_list('quiz_id', flat=True)
    )

    return render(request, "admin_panel/manage-olympiad-questions.html", {
        'exam': exam,
        'direct_questions': direct_questions,
        'assigned_quizzes': assigned_quizzes,
        'available_quizzes': available_quizzes,
        'question_types': OlympiadQuestion.QUESTION_TYPES,
        'difficulties': OlympiadQuestion.DIFFICULTY,
    })