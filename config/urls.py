"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    # Admin Panel (Django admin)
    path('admin/', admin.site.urls),

    # API Routes
    path('accounts/', include('accounts.urls')),      # Login, signup, profile API
    path('courses/', include('courses.urls')),        # Courses, quiz, enrollment API
    path('api/', include('institutions.urls')),       # Institutions & Students API

    # Frontend Routes (HTML Templates)
    # This already includes /ai-books/, /admin-panel/courses/, and now
    # /admin-panel/books/ + /admin-panel/books/add/ — see frontend/urls.py.
    path('', include('frontend.urls')),
]

# Serve static and media files in development.
# In production this must be handled by the web server / a storage service instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'frontend.views.handler404'