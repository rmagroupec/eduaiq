from django.shortcuts import render


# ==========================
# Error Pages
# ==========================

def handler404(request, exception=None):
    """Custom 404 Page"""
    return render(request, "404page.html", status=404)


# ==========================
# Website Views
# ==========================

def home(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def courses(request):
    return render(request, "courses.html")


# ==========================
# Admin Panel Views
# ==========================

def dashboard(request):
    return render(request, "admin_panel/dashboard.html")


def users(request):
    return render(request, "admin_panel/users.html")