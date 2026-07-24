from django.db import models

class Institution(models.Model):
    TYPE_CHOICES = [('school', 'School'), ('college', 'College')]
    STATUS_CHOICES = [('active', 'Active'), ('pending', 'Pending'), ('suspended', 'Suspended')]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    board_affiliation = models.CharField(max_length=100, blank=True)  # CBSE/ICSE/State/Univ
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    admin_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                    related_name='managed_institution')
    onboarded_by_partner = models.ForeignKey('partners.Partner', null=True, blank=True,
                                              on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class InstitutionStudent(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='students')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                 limit_choices_to={'role': 'student'})
    admission_no = models.CharField(max_length=50)
    class_grade = models.CharField(max_length=20)
    section = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ('institution', 'student')