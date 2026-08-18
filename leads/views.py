"""
CRM Views — Pure JSON API (mirrors institutions/views.py conventions).
No template rendering. Every view returns JsonResponse.

Access model: the CRM is an internal sales tool.
- Staff (is_staff/is_superuser or role in staff-ish roles) can see and manage
  every record.
- Any other authenticated "sales" user only sees/manages records where they
  are the `owner` (or `created_by`, for records with no owner concept).
- Everyone else (anonymous, students, parents, institution admins) is
  forbidden outright — these are internal sales records, never public.
"""

import json
import math
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models as dj_models
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from institutions.forms import StudentForm
from institutions.models import Institution, Student

from .forms import ActivityForm, LeadForm, OpportunityForm, SalesTargetForm, StudentInquiryForm
from .models import Activity, Lead, Opportunity, SalesTarget, StudentInquiry


# ============================================================================
# HELPERS
# ============================================================================

def _body(request):
    data = {}
    if request.content_type.startswith('application/json') and request.body:
        try:
            data = json.loads(request.body)
        except (ValueError, TypeError):
            pass
    else:
        data = request.POST.dict()
    return data


def _is_staff(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) in ('staff', 'super_admin', 'admin', 'sales_manager') or
        getattr(user, 'is_staff', False) or
        getattr(user, 'is_superuser', False)
    )


def _is_crm_user(user):
    """Anyone allowed to touch the CRM at all: staff, or an in-house sales rep."""
    if not user.is_authenticated:
        return False
    return _is_staff(user) or getattr(user, 'role', None) in ('sales', 'sales_manager', 'partner')


def _form_errors(form):
    return {field: errs for field, errs in form.errors.items()}


def _bind_form_for_update(form_class, instance, request, body):
    if request.method == 'PUT':
        return form_class(body, instance=instance)

    mergeable_fields = list(form_class._meta.fields)
    existing = model_to_dict(instance, fields=mergeable_fields)
    merged = dict(existing)
    merged.update(body)
    return form_class(merged, instance=instance)


def _paginate(request, qs, serializer_fn, default_page_size=20, **serializer_kwargs):
    try:
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(max(int(request.GET.get('page_size', default_page_size)), 1), 100)
    except ValueError:
        page, page_size = 1, default_page_size

    count = qs.count()
    total_pages = math.ceil(count / page_size) if count else 0
    start = (page - 1) * page_size
    results = qs[start:start + page_size]

    return {
        'count': count,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': [serializer_fn(obj, **serializer_kwargs) for obj in results],
    }


def _owned_or_all(user, qs, owner_field='owner'):
    """Staff sees everything; a sales rep only sees their own records."""
    if _is_staff(user):
        return qs
    return qs.filter(**{owner_field: user})


def _user_brief(u):
    if not u:
        return None
    return {'id': u.id, 'name': u.get_full_name() or u.username, 'role': getattr(u, 'role', '')}


# ============================================================================
# SERIALIZERS
# ============================================================================

def serialize_lead(l, detailed=False):
    data = {
        'id': l.id,
        'lead_name': l.lead_name,
        'institution_name': l.institution_name,
        'institution_type': l.institution_type,
        'phone': l.phone,
        'email': l.email,
        'city': l.city,
        'state': l.state,
        'stage': l.stage,
        'priority': l.priority,
        'source': l.source,
        'owner': _user_brief(l.owner),
        'next_follow_up_date': l.next_follow_up_date,
        'is_open': l.is_open,
        'created_at': l.created_at.isoformat() if l.created_at else None,
    }
    if detailed:
        data.update({
            'designation': l.designation,
            'partner_id': l.partner_id,
            'partner_referral_code': l.partner.referral_code if l.partner_id else None,
            'expected_seats': l.expected_seats,
            'interested_plan_id': l.interested_plan_id,
            'interested_plan_name': l.interested_plan.name if l.interested_plan_id else None,
            'lost_reason': l.lost_reason,
            'notes': l.notes,
            'converted_institution_id': l.converted_institution_id,
            'converted_at': l.converted_at.isoformat() if l.converted_at else None,
            'created_by': _user_brief(l.created_by),
            'updated_at': l.updated_at.isoformat() if l.updated_at else None,
            'open_opportunity_value': (
                l.opportunities.exclude(stage__in=['won', 'lost'])
                .aggregate(total=dj_models.Sum('amount'))['total'] or 0
            ),
        })
    return data


def serialize_inquiry(s, detailed=False):
    data = {
        'id': s.id,
        'student_name': s.student_name,
        'guardian_name': s.guardian_name,
        'phone': s.phone,
        'email': s.email,
        'city': s.city,
        'class_grade_interested': s.class_grade_interested,
        'stage': s.stage,
        'priority': s.priority,
        'source': s.source,
        'owner': _user_brief(s.owner),
        'next_follow_up_date': s.next_follow_up_date,
        'is_open': s.is_open,
        'created_at': s.created_at.isoformat() if s.created_at else None,
    }
    if detailed:
        data.update({
            'interested_institution_id': s.interested_institution_id,
            'interested_institution_name': s.interested_institution.name if s.interested_institution_id else None,
            'interested_course_id': s.interested_course_id,
            'interested_course_title': s.interested_course.title if s.interested_course_id else None,
            'interested_in_olympiad': s.interested_in_olympiad,
            'lost_reason': s.lost_reason,
            'notes': s.notes,
            'converted_student_id': s.converted_student_id,
            'converted_at': s.converted_at.isoformat() if s.converted_at else None,
            'created_by': _user_brief(s.created_by),
            'updated_at': s.updated_at.isoformat() if s.updated_at else None,
        })
    return data


def serialize_opportunity(o, detailed=False):
    data = {
        'id': o.id,
        'name': o.name,
        'stage': o.stage,
        'amount': str(o.amount),
        'probability_pct': o.probability_pct,
        'weighted_amount': str(o.weighted_amount),
        'owner': _user_brief(o.owner),
        'lead_id': o.lead_id,
        'lead_name': o.lead.lead_name if o.lead_id else None,
        'student_inquiry_id': o.student_inquiry_id,
        'student_inquiry_name': o.student_inquiry.student_name if o.student_inquiry_id else None,
        'expected_close_date': o.expected_close_date,
        'actual_close_date': o.actual_close_date,
        'created_at': o.created_at.isoformat() if o.created_at else None,
    }
    if detailed:
        data.update({
            'plan_id': o.plan_id,
            'plan_name': o.plan.name if o.plan_id else None,
            'linked_transaction_id': o.linked_transaction_id,
            'notes': o.notes,
            'updated_at': o.updated_at.isoformat() if o.updated_at else None,
        })
    return data


def serialize_activity(a):
    return {
        'id': a.id,
        'lead_id': a.lead_id,
        'student_inquiry_id': a.student_inquiry_id,
        'opportunity_id': a.opportunity_id,
        'activity_type': a.activity_type,
        'notes': a.notes,
        'due_date': a.due_date.isoformat() if a.due_date else None,
        'is_completed': a.is_completed,
        'created_by': _user_brief(a.created_by),
        'created_at': a.created_at.isoformat() if a.created_at else None,
    }


def serialize_target(t):
    return {
        'id': t.id,
        'owner': _user_brief(t.owner),
        'partner_id': t.partner_id,
        'partner_referral_code': t.partner.referral_code if t.partner_id else None,
        'period_type': t.period_type,
        'period_start': t.period_start,
        'period_end': t.period_end,
        'target_amount': str(t.target_amount),
        'achieved_amount': str(t.achieved_amount),
        'achievement_pct': t.achievement_pct,
    }


# ============================================================================
# LEADS (Institution / Franchise — B2B)
# ============================================================================

@login_required
@require_http_methods(['GET', 'POST'])
def lead_list(request):
    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        qs = Lead.objects.select_related('partner', 'owner', 'interested_plan').all()
        qs = _owned_or_all(request.user, qs)

        stage = request.GET.get('stage')
        if stage:
            qs = qs.filter(stage=stage)
        priority = request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        owner_id = request.GET.get('owner')
        if owner_id:
            qs = qs.filter(owner_id=owner_id)
        search = request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                dj_models.Q(lead_name__icontains=search) |
                dj_models.Q(institution_name__icontains=search) |
                dj_models.Q(phone__icontains=search)
            )

        payload = _paginate(request, qs, serialize_lead, detailed=request.GET.get('detailed') == 'true')
        return JsonResponse(payload)

    body = _body(request)
    body.setdefault('stage', 'new')
    body.setdefault('priority', 'medium')
    body.setdefault('source', 'website')
    form = LeadForm(body)
    if form.is_valid():
        lead = form.save(commit=False)
        lead.created_by = request.user
        try:
            lead.full_clean()
            lead.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'lead': serialize_lead(lead, detailed=True)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_lead_or_404(pk):
    try:
        return Lead.objects.select_related('partner', 'owner', 'interested_plan').get(pk=pk)
    except ObjectDoesNotExist:
        return None


def _can_touch(user, owner_id):
    return _is_staff(user) or owner_id == user.id


@login_required
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def lead_detail(request, pk):
    lead = _get_lead_or_404(pk)
    if lead is None:
        return JsonResponse({'error': 'Lead not found'}, status=404)
    if not _is_crm_user(request.user) or not _can_touch(request.user, lead.owner_id):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        return JsonResponse({'lead': serialize_lead(lead, detailed=True)})

    if request.method == 'DELETE':
        lead.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(LeadForm, lead, request, body)
    if form.is_valid():
        lead = form.save(commit=False)
        try:
            lead.full_clean()
            lead.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'lead': serialize_lead(lead, detailed=True)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


@login_required
@require_http_methods(['POST'])
def lead_convert(request, pk):
    """Convert a Lead into a live Institution record."""
    lead = _get_lead_or_404(pk)
    if lead is None:
        return JsonResponse({'error': 'Lead not found'}, status=404)
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Only staff can convert a lead into an Institution.'}, status=403)
    if lead.stage == 'converted' and lead.converted_institution_id:
        return JsonResponse({'error': 'This lead has already been converted.'}, status=400)

    body = _body(request)
    inst_type = body.get('type') or ('school' if lead.institution_type != 'college' else 'college')
    institution = Institution(
        name=body.get('name') or lead.institution_name or lead.lead_name,
        type=inst_type,
        board_affiliation=body.get('board_affiliation', ''),
        address=body.get('address') or 'Address pending — update after conversion',
        city=body.get('city') or lead.city,
        state=body.get('state') or lead.state,
        admin_user_id=body.get('admin_user') or None,
        onboarded_by_partner=lead.partner,
        status='pending',
    )
    try:
        institution.full_clean(exclude=['admin_user'])
        institution.save()
    except DjangoValidationError as e:
        return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)

    lead.stage = 'converted'
    lead.converted_institution = institution
    lead.converted_at = timezone.now()
    lead.save(update_fields=['stage', 'converted_institution', 'converted_at', 'updated_at'])

    return JsonResponse({
        'success': True,
        'institution_id': institution.id,
        'lead': serialize_lead(lead, detailed=True),
    }, status=201)


# ============================================================================
# STUDENT INQUIRIES (Admission / Course Enquiry — B2C)
# ============================================================================

@login_required
@require_http_methods(['GET', 'POST'])
def inquiry_list(request):
    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        qs = StudentInquiry.objects.select_related('owner', 'interested_institution', 'interested_course').all()
        qs = _owned_or_all(request.user, qs)

        stage = request.GET.get('stage')
        if stage:
            qs = qs.filter(stage=stage)
        priority = request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        search = request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                dj_models.Q(student_name__icontains=search) |
                dj_models.Q(guardian_name__icontains=search) |
                dj_models.Q(phone__icontains=search)
            )

        payload = _paginate(request, qs, serialize_inquiry, detailed=request.GET.get('detailed') == 'true')
        return JsonResponse(payload)

    body = _body(request)
    body.setdefault('stage', 'new')
    body.setdefault('priority', 'medium')
    body.setdefault('source', 'website')
    body.setdefault('interested_in_olympiad', False)
    form = StudentInquiryForm(body)
    if form.is_valid():
        inquiry = form.save(commit=False)
        inquiry.created_by = request.user
        try:
            inquiry.full_clean()
            inquiry.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'inquiry': serialize_inquiry(inquiry, detailed=True)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_inquiry_or_404(pk):
    try:
        return StudentInquiry.objects.select_related('owner', 'interested_institution', 'interested_course').get(pk=pk)
    except ObjectDoesNotExist:
        return None


@login_required
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def inquiry_detail(request, pk):
    inquiry = _get_inquiry_or_404(pk)
    if inquiry is None:
        return JsonResponse({'error': 'Student inquiry not found'}, status=404)
    if not _is_crm_user(request.user) or not _can_touch(request.user, inquiry.owner_id):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        return JsonResponse({'inquiry': serialize_inquiry(inquiry, detailed=True)})

    if request.method == 'DELETE':
        inquiry.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(StudentInquiryForm, inquiry, request, body)
    if form.is_valid():
        inquiry = form.save(commit=False)
        try:
            inquiry.full_clean()
            inquiry.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'inquiry': serialize_inquiry(inquiry, detailed=True)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


@login_required
@require_http_methods(['POST'])
def inquiry_convert(request, pk):
    """
    Convert a Student Inquiry into a live Student record.
    """
    inquiry = _get_inquiry_or_404(pk)
    if inquiry is None:
        return JsonResponse({'error': 'Student inquiry not found'}, status=404)
    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if inquiry.stage == 'enrolled' and inquiry.converted_student_id:
        return JsonResponse({'error': 'This inquiry has already been converted.'}, status=400)

    body = _body(request)
    body.setdefault('institution', inquiry.interested_institution_id)
    form = StudentForm(body)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)

    student = form.save(commit=False)
    try:
        student.full_clean()
        student.save()
    except DjangoValidationError as e:
        return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)

    inquiry.stage = 'enrolled'
    inquiry.converted_student = student
    inquiry.converted_at = timezone.now()
    inquiry.save(update_fields=['stage', 'converted_student', 'converted_at', 'updated_at'])

    return JsonResponse({
        'success': True,
        'student_id': student.id,
        'inquiry': serialize_inquiry(inquiry, detailed=True),
    }, status=201)


# ============================================================================
# OPPORTUNITIES (Sales pipeline / deals)
# ============================================================================

@login_required
@require_http_methods(['GET', 'POST'])
def opportunity_list(request):
    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        qs = Opportunity.objects.select_related('lead', 'student_inquiry', 'owner', 'plan').all()
        qs = _owned_or_all(request.user, qs)

        stage = request.GET.get('stage')
        if stage:
            qs = qs.filter(stage=stage)
        lead_id = request.GET.get('lead')
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        student_inquiry_id = request.GET.get('student_inquiry')
        if student_inquiry_id:
            qs = qs.filter(student_inquiry_id=student_inquiry_id)

        payload = _paginate(request, qs, serialize_opportunity, detailed=request.GET.get('detailed') == 'true')
        payload['pipeline_total'] = str(
            qs.exclude(stage__in=['won', 'lost']).aggregate(t=dj_models.Sum('amount'))['t'] or 0
        )
        return JsonResponse(payload)

    body = _body(request)
    body.setdefault('stage', 'prospecting')
    body.setdefault('probability_pct', 20)
    form = OpportunityForm(body)
    if form.is_valid():
        opp = form.save(commit=False)
        try:
            opp.full_clean()
            opp.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'opportunity': serialize_opportunity(opp, detailed=True)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_opportunity_or_404(pk):
    try:
        return Opportunity.objects.select_related('lead', 'student_inquiry', 'owner', 'plan').get(pk=pk)
    except ObjectDoesNotExist:
        return None


@login_required
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def opportunity_detail(request, pk):
    opp = _get_opportunity_or_404(pk)
    if opp is None:
        return JsonResponse({'error': 'Opportunity not found'}, status=404)
    if not _is_crm_user(request.user) or not _can_touch(request.user, opp.owner_id):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        return JsonResponse({'opportunity': serialize_opportunity(opp, detailed=True)})

    if request.method == 'DELETE':
        opp.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(OpportunityForm, opp, request, body)
    if form.is_valid():
        opp = form.save(commit=False)
        if opp.stage == 'won' and not opp.actual_close_date:
            opp.actual_close_date = date.today()
        try:
            opp.full_clean()
            opp.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'opportunity': serialize_opportunity(opp, detailed=True)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# ACTIVITIES (Follow-ups & logs)
# ============================================================================

@login_required
@require_http_methods(['GET', 'POST'])
def activity_list(request):
    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        qs = Activity.objects.select_related('lead', 'student_inquiry', 'opportunity', 'created_by').all()
        if not _is_staff(request.user):
            qs = qs.filter(created_by=request.user)

        lead_id = request.GET.get('lead')
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        inquiry_id = request.GET.get('student_inquiry')
        if inquiry_id:
            qs = qs.filter(student_inquiry_id=inquiry_id)
        opp_id = request.GET.get('opportunity')
        if opp_id:
            qs = qs.filter(opportunity_id=opp_id)

        payload = _paginate(request, qs, serialize_activity)
        return JsonResponse(payload)

    body = _body(request)
    form = ActivityForm(body)
    if form.is_valid():
        act = form.save(commit=False)
        act.created_by = request.user
        try:
            act.full_clean()
            act.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'activity': serialize_activity(act)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


@login_required
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def activity_detail(request, pk):
    try:
        act = Activity.objects.select_related('created_by').get(pk=pk)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Activity not found'}, status=404)

    if not _is_crm_user(request.user) or not _can_touch(request.user, act.created_by_id):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        return JsonResponse({'activity': serialize_activity(act)})

    if request.method == 'DELETE':
        act.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(ActivityForm, act, request, body)
    if form.is_valid():
        act = form.save(commit=False)
        try:
            act.full_clean()
            act.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'activity': serialize_activity(act)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# SALES TARGETS
# ============================================================================

@login_required
@require_http_methods(['GET', 'POST'])
def target_list(request):
    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        qs = SalesTarget.objects.select_related('owner', 'partner').all()
        qs = _owned_or_all(request.user, qs)

        payload = _paginate(request, qs, serialize_target)
        return JsonResponse(payload)

    if not _is_staff(request.user):
        return JsonResponse({'error': 'Only staff can create sales targets.'}, status=403)

    body = _body(request)
    form = SalesTargetForm(body)
    if form.is_valid():
        target = form.save(commit=False)
        try:
            target.full_clean()
            target.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'target': serialize_target(target)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


@login_required
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def target_detail(request, pk):
    try:
        target = SalesTarget.objects.select_related('owner', 'partner').get(pk=pk)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Sales target not found'}, status=404)

    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        return JsonResponse({'target': serialize_target(target)})

    if not _is_staff(request.user):
        return JsonResponse({'error': 'Only staff can update/delete sales targets.'}, status=403)

    if request.method == 'DELETE':
        target.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(SalesTargetForm, target, request, body)
    if form.is_valid():
        target = form.save(commit=False)
        try:
            target.full_clean()
            target.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'target': serialize_target(target)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# CRM DASHBOARD (Pipeline Overview & Metrics)
# ============================================================================

@login_required
@require_GET
def crm_dashboard(request):
    if not _is_crm_user(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    today = date.today()
    now = timezone.now()
    first_of_month = today.replace(day=1)

    opps_qs = _owned_or_all(request.user, Opportunity.objects.all())
    leads_qs = _owned_or_all(request.user, Lead.objects.all())
    inquiries_qs = _owned_or_all(request.user, StudentInquiry.objects.all())

    # Opportunity calculations
    open_opps = opps_qs.exclude(stage__in=['won', 'lost'])
    open_pipeline_val = open_opps.aggregate(total=dj_models.Sum('amount'))['total'] or 0

    weighted_pipeline_val = sum(o.weighted_amount for o in open_opps)

    won_this_month_val = opps_qs.filter(
        stage='won',
        actual_close_date__gte=first_of_month,
    ).aggregate(total=dj_models.Sum('amount'))['total'] or 0

    # Overdue followups count
    overdue_leads = leads_qs.filter(next_follow_up_date__lt=today).exclude(stage__in=['converted', 'lost']).count()
    overdue_inquiries = inquiries_qs.filter(next_follow_up_date__lt=today).exclude(stage__in=['enrolled', 'lost']).count()
    overdue_activities = Activity.objects.filter(due_date__lt=now, is_completed=False).count()
    total_overdue = overdue_leads + overdue_inquiries + overdue_activities

    # Funnel breakdowns
    leads_total = leads_qs.count()
    leads_open = leads_qs.exclude(stage__in=['converted', 'lost']).count()
    leads_by_stage = {st: leads_qs.filter(stage=st).count() for st, _ in Lead.STAGE_CHOICES}

    inquiries_total = inquiries_qs.count()
    inquiries_open = inquiries_qs.exclude(stage__in=['enrolled', 'lost']).count()
    inquiries_by_stage = {st: inquiries_qs.filter(stage=st).count() for st, _ in StudentInquiry.STAGE_CHOICES}

    # Opportunities stage breakdown & win rate
    opps_by_stage = {st: opps_qs.filter(stage=st).count() for st, _ in Opportunity.STAGE_CHOICES}
    won_count = opps_qs.filter(stage='won').count()
    lost_count = opps_qs.filter(stage='lost').count()
    open_count = open_opps.count()
    total_closed = won_count + lost_count
    win_rate_pct = round((won_count / total_closed * 100), 1) if total_closed > 0 else 0

    # 6-Month Monthly Trend (Revenue Won vs Forecast)
    from datetime import timedelta
    months_labels = []
    monthly_won = []
    monthly_forecast = []
    
    for i in range(5, -1, -1):
        # Determine target month
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        m_start = date(year, month, 1)
        if month == 12:
            m_next = date(year + 1, 1, 1)
        else:
            m_next = date(year, month + 1, 1)

        w_val = opps_qs.filter(
            stage='won',
            actual_close_date__gte=m_start,
            actual_close_date__lt=m_next
        ).aggregate(total=dj_models.Sum('amount'))['total'] or 0

        f_val = opps_qs.filter(
            expected_close_date__gte=m_start,
            expected_close_date__lt=m_next
        ).aggregate(total=dj_models.Sum('amount'))['total'] or 0

        months_labels.append(m_start.strftime('%b'))
        monthly_won.append(float(w_val))
        monthly_forecast.append(float(f_val))

    # Recent High-Value Deals
    recent_deals = [
        serialize_opportunity(o, detailed=True) 
        for o in opps_qs.select_related('lead', 'student_inquiry', 'owner').order_by('-amount')[:5]
    ]

    return JsonResponse({
        'opportunities': {
            'open_pipeline_value': str(open_pipeline_val),
            'weighted_pipeline_value': str(round(weighted_pipeline_val, 2)),
            'won_this_month': str(won_this_month_val),
            'by_stage': opps_by_stage,
            'won_count': won_count,
            'lost_count': lost_count,
            'open_count': open_count,
            'win_rate_pct': win_rate_pct,
        },
        'overdue_followups': total_overdue,
        'leads': {
            'total': leads_total,
            'open': leads_open,
            'by_stage': leads_by_stage,
        },
        'student_inquiries': {
            'total': inquiries_total,
            'open': inquiries_open,
            'by_stage': inquiries_by_stage,
        },
        'monthly_trend': {
            'categories': months_labels,
            'won_series': monthly_won,
            'forecast_series': monthly_forecast,
        },
        'recent_deals': recent_deals,
    })

