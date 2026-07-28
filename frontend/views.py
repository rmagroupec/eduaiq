from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


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


# ==========================
# Admin Panel Views
# ==========================

def dashboard(request):
    """Admin dashboard"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return render(request, "404page.html", status=403)
    return render(request, "admin_panel/dashboard.html")


def users(request):
    """Admin users management"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return render(request, "404page.html", status=403)
    return render(request, "admin_panel/users.html")


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


def single_page(request):
    """Single page (generic)"""
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
def login_view(request):
    return render(request, 'admin_panel/login.html')

def register_view(request):
    return render(request, 'admin_panel/register.html')


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

