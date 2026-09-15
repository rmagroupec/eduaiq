from django import forms

from .models import Activity, Lead, Opportunity, SalesTarget, StudentInquiry


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'partner', 'owner', 'source', 'lead_name', 'institution_name', 'institution_type',
            'designation', 'phone', 'email', 'city', 'state', 'stage', 'priority',
            'expected_seats', 'interested_plan', 'next_follow_up_date', 'lost_reason', 'notes',
        ]


class StudentInquiryForm(forms.ModelForm):
    class Meta:
        model = StudentInquiry
        fields = [
            'owner', 'source', 'student_name', 'guardian_name', 'phone', 'email', 'city',
            'class_grade_interested', 'interested_institution', 'interested_course',
            'interested_in_olympiad', 'stage', 'priority', 'next_follow_up_date',
            'lost_reason', 'notes',
        ]


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            'lead', 'student_inquiry', 'name', 'owner', 'amount', 'probability_pct', 'stage',
            'expected_close_date', 'actual_close_date', 'plan', 'linked_transaction', 'notes',
        ]


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            'lead', 'student_inquiry', 'opportunity', 'activity_type', 'notes',
            'due_date', 'is_completed',
        ]


class SalesTargetForm(forms.ModelForm):
    class Meta:
        model = SalesTarget
        fields = ['owner', 'partner', 'period_type', 'period_start', 'period_end', 'target_amount']
