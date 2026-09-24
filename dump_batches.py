import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from institutions.models import Batch, Institution

print("Institutions:")
for inst in Institution.objects.all():
    print(f" - {inst.id}: {inst.name}")

print("\nBatches:")
for b in Batch.objects.all():
    print(f" - {b.id}: {b.name} (Inst: {b.institution_id}) (Exam: {b.target_exam})")
