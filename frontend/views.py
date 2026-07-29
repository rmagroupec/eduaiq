from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

User = get_user_model()


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
    """Homepage - Featured courses and categories"""
    return render(request, "index.html")


def about(request):
    """About page"""
    return render(request, "about.html")


def courses(request):
    """
    All courses listing page
    Template: courses.html (or product-archive.html)
    API: GET /courses/courses/?page=1&page_size=12
    """
    return render(request, "courses.html")


def course_detail(request):
    """
    Single course detail page with modules, lessons, and quizzes
    Template: course-detail.html
    API: GET /courses/courses/{slug}/
    Query Params: slug (course slug)
    """
    course_slug = request.GET.get('slug', '')
    return render(request, "course-detail.html", {
        'course_slug': course_slug
    })


def categories(request):
    """
    Course categories listing
    Template: categories.html
    API: GET /courses/categories/
    """
    return render(request, "categories.html")


def search(request):
    """
    Search results page
    Template: search.html
    API: GET /courses/courses/?q=search_query
    Query Params: q (search query)
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
    """AI Books page"""
    return render(request, "ai-books.html")


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

@login_required(login_url='/admin-panel/login/')
def my_learning(request):
    """
    Student learning dashboard - shows enrolled courses and progress
    Template: my-learning.html
    API: GET /courses/my-enrollments/?page=1
    Requires: User authentication
    """
    return render(request, "my-learning.html")


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
    Admin dashboard.

    NOTE: previously this also required request.user.is_staff, which meant a
    freshly self-registered account (student/teacher/parent/etc.) could log
    in successfully but would still get bounced with a 403 on the very next
    page. Since signup no longer grants is_staff by default, this now only
    requires the user to be logged in so "login -> dashboard" actually works.
    If you want a real staff-only admin area later, add a separate URL/view
    for that instead of gating the main post-login landing page on is_staff.
    """
    return render(request, "admin_panel/index.html")


@login_required(login_url='/admin-panel/login/')
def users(request):
    """Admin users management"""
    return render(request, "admin_panel/users.html")


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
def admin_page_router(request, page_name):
    """
    Dynamic router for admin panel views.
    Maps /admin-panel/<page_name>/ to template: admin_panel/<page_name>.html
    """
    from django.template.loader import get_template
    from django.template import TemplateDoesNotExist

    mapping = {
        'courses': 'admin_panel/course-list.html',
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
def login_view(request):
    """
    GET  -> login form dikhata hai
    POST -> username YA email dono se login allow karta hai
    """
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
            return redirect('admin_panel')   # ✅ login -> dashboard

        return render(request, 'admin_panel/login.html', {
            'form_errors': ["Invalid username or password."],
            'old_username': identifier,
        })

    return render(request, 'admin_panel/login.html')



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
    return redirect('login')


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