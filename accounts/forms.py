"""
Account Forms
Built against the real User / Profile / Role models.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Profile


class SignUpForm(UserCreationForm):
    """
    Registration form. `phone` and `role` are required on the User model,
    so they're collected here alongside the standard username/password fields.
    """
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, max_length=15)
    role = forms.CharField(required=True, max_length=100)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'email', 'phone', 'role',
            'password1', 'password2',
        )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone


class UserEditForm(forms.ModelForm):
    """Edit the core User fields (name, contact, personal/professional details)."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'profile_image',
            'date_of_birth', 'gender', 'caste_category', 'marital_status',
            'father_name', 'mother_name', 'qualification', 'experience',
            'contract_type', 'shift', 'joining_date', 'school_name',
            'academic_year', 'facebook', 'instagram', 'linkedin',
            'description',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This phone number is already in use.')
        return phone


class ProfileForm(forms.ModelForm):
    """Edit the address-related Profile fields."""

    class Meta:
        model = Profile
        fields = ['address', 'city', 'state', 'pincode']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class DeleteAccountForm(forms.Form):
    """Requires the current password as confirmation before deleting the account."""
    password = forms.CharField(widget=forms.PasswordInput, label='Confirm your password')

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data['password']
        if self.user is None or not self.user.check_password(password):
            raise forms.ValidationError('Incorrect password.')
        return password