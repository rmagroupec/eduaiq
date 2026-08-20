from django import forms

from .models import Institution, Student, Batch


class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = [
            'name', 'type', 'board_affiliation', 'address', 'city', 'state',
            'admin_user', 'onboarded_by_partner', 'created_by', 'assigned_employee', 'status',
        ]


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = [
            'institution', 'name', 'code', 'target_exam', 'start_date', 'end_date', 'is_active'
        ]


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'user', 'institution', 'batch', 'admission_no', 'roll_number', 'class_grade', 'section',
            'academic_year', 'admission_date', 'date_of_birth', 'gender', 'blood_group',
            'category', 'father_name', 'mother_name', 'guardian_name', 'guardian_relation',
            'guardian_phone', 'guardian_email', 'parent_user', 'aadhar_or_id_proof',
            'profile_photo', 'emergency_contact_phone', 'status',
        ]