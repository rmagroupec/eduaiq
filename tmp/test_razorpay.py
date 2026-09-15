import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
import json

c = Client()
res = c.post('/payments/api/payment/create-order/', data=json.dumps({'amount': 299}), content_type='application/json', HTTP_HOST='127.0.0.1')
print('STATUS:', res.status_code)
data = res.json()
for k, v in data.items():
    print(f'  {k}: {v}')
