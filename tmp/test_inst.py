import os
import sys
import django

sys.path.insert(0, r'E:\Rackle Infotech\eduaiq-fixed\eduaiq')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from frontend.views import dashboard

User = get_user_model()
rf = RequestFactory()

u = User.objects.filter(username='institute_login').first()
if u:
    req = rf.get('/admin-panel/dashboard/')
    req.user = u
    resp = dashboard(req)
    print(f"User: {u.username}, Role: {getattr(u, 'role', None)}")
    print(f"Status: {resp.status_code}")
    html = resp.content.decode('utf-8')
    import re
    unparsed = re.findall(r'\{\{\s*inst_data[^}]*\}\}', html)
    print("UNPARSED INST TAGS IN HTML:", unparsed)
    
    # Check course count and books count in html
    match_courses = re.search(r'Allowed Courses</span>\s*<h3[^>]*>(\d+)</h3>', html)
    match_books = re.search(r'Allowed AI Books</span>\s*<h3[^>]*>(\d+)</h3>', html)
    if match_courses:
        print(f"Rendered Allowed Courses Count: {match_courses.group(1)}")
    if match_books:
        print(f"Rendered Allowed AI Books Count: {match_books.group(1)}")
