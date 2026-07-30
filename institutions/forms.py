from django import forms

from .models import Institution, Student


class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = [
            'name', 'type', 'board_affiliation', 'address', 'city', 'state',
            'admin_user', 'onboarded_by_partner', 'status',
        ]


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'user', 'institution', 'admission_no', 'roll_number', 'class_grade', 'section',
            'academic_year', 'admission_date', 'date_of_birth', 'gender', 'blood_group',
            'category', 'father_name', 'mother_name', 'guardian_name', 'guardian_relation',
            'guardian_phone', 'guardian_email', 'parent_user', 'aadhar_or_id_proof',
            'profile_photo', 'emergency_contact_phone', 'status',
        ]