import os
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, Attendance

def seed_attendance():
    users = User.objects.all()
    if not users.exists():
        print("No users found to seed attendance for.")
        return

    statuses = ['P', 'P', 'P', 'P', 'A', 'H', 'F', 'L']
    academic_year = 'Jun 2025/2026'

    # Seed data for Jan - May 2025/2026
    start_date = date(2025, 1, 1)
    end_date = date(2025, 5, 31)

    records_to_create = []

    for user in users:
        curr_date = start_date
        while curr_date <= end_date:
            # Skip Sundays
            if curr_date.weekday() != 6:
                status = random.choice(statuses)
                records_to_create.append(
                    Attendance(
                        user=user,
                        date=curr_date,
                        status=status,
                        academic_year=academic_year,
                        remarks="Automated Record"
                    )
                )
            else:
                # Sunday Holiday
                records_to_create.append(
                    Attendance(
                        user=user,
                        date=curr_date,
                        status='H',
                        academic_year=academic_year,
                        remarks="Sunday"
                    )
                )
            curr_date += timedelta(days=1)

    Attendance.objects.filter(academic_year=academic_year).delete()
    Attendance.objects.bulk_create(records_to_create, ignore_conflicts=True)
    print(f"Successfully seeded {len(records_to_create)} attendance records into SQLite database.")

if __name__ == '__main__':
    seed_attendance()
