import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from accounts.models import User
c = Client()
u = User.objects.filter(is_superuser=True).first()
c.force_login(u)

res = c.post('/api/institutions/5/allot-courses/', data={'course_ids': [1,2,3]}, content_type='application/json')
print('Status:', res.status_code)

if res.status_code == 500:
    import re
    m = re.search(r'<div class="exception_value">(.*?)</div>', res.content.decode(), re.S)
    if m:
        print(m.group(1).strip())
    else:
        print("Could not parse exception value. Content snippet:")
        print(res.content.decode()[:1000])
