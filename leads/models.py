from django.db import models

class Lead(models.Model):
    STAGE_CHOICES = [('new', 'New'), ('contacted', 'Contacted'), ('demo', 'Demo Scheduled'),
                      ('converted', 'Converted'), ('lost', 'Lost')]

    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE, related_name='leads')
    lead_name = models.CharField(max_length=150)
    institution_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    converted_institution = models.ForeignKey('institutions.Institution', null=True, blank=True,
                                               on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)