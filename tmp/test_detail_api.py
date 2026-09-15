import os
import sys
import django

sys.path.insert(0, r'E:\Rackle Infotech\eduaiq-fixed\eduaiq')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from courses.views import CourseDetailAPIView

factory = RequestFactory()
view = CourseDetailAPIView.as_view()

req = factory.get('/courses/courses/full-stack-development-with-ai/', HTTP_HOST='127.0.0.1')
req.user = AnonymousUser()
res = view(req, slug='full-stack-development-with-ai')
print("Status code:", res.status_code)
if hasattr(res, 'data'):
    print("Data:", res.data)
else:
    print("Content:", res.content)
