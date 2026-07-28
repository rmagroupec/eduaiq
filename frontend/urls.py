from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # ==========================
    # Main Website Pages
    # ==========================
    path('', views.home, name='home'),                                    # Homepage
    path('about/', views.about, name='about'),                            # About page
    path('contact/', views.contact, name='contact'),                      # Contact page
    path('faq/', views.faq, name='faq'),                                  # FAQ page
    
    # ==========================
    # Course Pages (Public)
    # ==========================
    path('courses/', views.courses, name='courses'),                      # All courses listing
    path('course/', views.course_detail, name='course_detail'),           # Single course detail
    path('categories/', views.categories, name='categories'),             # Course categories
    path('search/', views.search, name='search'),                         # Search results
    
    # ==========================
    # Learning Pages (Login Required)
    # ==========================
    path('my-learning/', views.my_learning, name='my_learning'),          # Student dashboard
    path('quiz/', views.quiz_player, name='quiz_player'),                 # Quiz player
    
    # ==========================
    # Feature Pages
    # ==========================
    path('skill-development/', views.skill_development, name='skill_development'),
    path('ai-lab/', views.ai_lab, name='ai_lab'),
    path('ai-books/', views.ai_books, name='ai_books'),
    path('olympiads/', views.olympiads, name='olympiads'),
    path('career/', views.career, name='career'),
    path('team/', views.team, name='team'),
    path('gallery/', views.gallery, name='gallery'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('facility/', views.facility, name='facility'),
    path('growth-partner-kit/', views.growth_partner_kit, name='growth_partner_kit'),
    path('apply-for-franchise/', views.apply_for_franchise, name='apply_for_franchise'),
    path('eduaiq-ecosystem/', views.eduaiq_ecosystem, name='eduaiq_ecosystem'),
    
    # ==========================
    # Blog & Content Pages
    # ==========================
    path('blog/', views.blog_archive, name='blog_archive'),
    path('blog/<slug:slug>/', views.single_blog, name='single_blog'),
    path('products/', views.product_archive, name='product_archive'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.product_cart, name='product_cart'),
    path('checkout/', views.product_checkout, name='product_checkout'),
    path('career/<slug:slug>/', views.career_detail, name='career_detail'),
    path('team/<slug:slug>/', views.team_detail, name='team_detail'),
    path('page/<slug:slug>/', views.single_page, name='single_page'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('legal-notice/', views.legal_notice, name='legal_notice'),
    
    # ==========================
    # Olympiad Pages
    # ==========================
    path('olympiad-curriculum/', views.olympiad_curriculum, name='olympiad_curriculum'),
    path('olympiad-form/', views.olympiad_form, name='olympiad_form'),
    
    # ==========================
    # Admin Panel Routes
    # ==========================
    path('admin-panel/dashboard/', views.dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.users, name='admin_users'),
    path('admin-panel/register/', views.register_view, name='register'),
    path('admin-panel/login/', views.login_view, name='login'),
]