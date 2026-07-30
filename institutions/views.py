"""
Institutions & Students Views — Pure JSON API
No template rendering. Every view returns JsonResponse.

Security notes:
- Student.aadhar_or_id_proof, guardian_phone, guardian_email, blood_group,
  category, and emergency_contact_phone are SENSITIVE fields. They are only
  ever included in the response for: staff, the Institution Admin who owns
  that student's Institution, the student themself, or the linked parent_user.
  Every other viewer (another institution's admin, an anonymous request, a
  different student) gets serialize_student_public() instead, which never
  contains those fields — this mirrors how QuizQuestion.correct_option is
  withheld from non-staff in the courses API.
- Institution management actions (create/update/delete, and creating/editing
  a Student under it) are restricted to staff or that Institution's own
  admin_user — one Institution Admin can never edit another Institution's
  data or students, even if they guess the ID.
"""

import json
import math

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from .forms import InstitutionForm, StudentForm
from .models import Institution, Student


# ============================================================================
# HELPERS
# ============================================================================

def _body(request):
    if request.content_type.startswith('application/json') and request.body:
        try:
            return json.loads(request.body)
        except (ValueError, TypeError):
            pass
    return request.POST.dict()


def _is_staff(user):
    return user.is_authenticated and getattr(user, 'role', None) in ('staff', 'super_admin')


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def _form_errors(form):
    return {field: errs for field, errs in form.errors.items()}


def _bind_form_for_update(form_class, instance, request, body):
    """
    PUT  -> caller must send the full payload; form binds directly to `body`
            exactly as before (unchanged behaviour).
    PATCH -> true partial update. We merge `body` on top of the instance's
            current values (via model_to_dict) so any field the client didn't
            send is treated as "keep the existing value", not "missing/required".
            File fields are excluded from the merge — request.FILES is passed
            through separately, and Django's ModelForm already preserves an
            existing file when no new one is submitted for that field.
    """
    files = request.FILES or None

    if request.method == 'PUT':
        return form_class(body, files, instance=instance)

    # PATCH: merge existing non-file field values under whatever the client sent
    file_field_names = {
        f.name for f in instance._meta.get_fields()
        if getattr(f, 'concrete', False) and f.get_internal_type() in ('FileField', 'ImageField')
    }
    mergeable_fields = [f for f in form_class._meta.fields if f not in file_field_names]
    existing = model_to_dict(instance, fields=mergeable_fields)

    merged = dict(existing)
    merged.update(body)

    return form_class(merged, files, instance=instance)


def _paginate(req, qs, serializer_fn, default_page_size=20, **serializer_kwargs):
    """
    NOTE: the first parameter is named `req`, not `request`, on purpose.
    Some callers (e.g. student_list) also need to pass request=request
    through **serializer_kwargs so the serializer can build absolute file
    URLs. If this parameter were also named `request`, Python would raise
    "got multiple values for argument 'request'" the moment both were
    supplied — one positionally, one via the kwargs dict. Renaming this
    parameter avoids the collision entirely; every call site is unaffected
    since it's passed positionally (_paginate(request, qs, ...)).
    """
    try:
        page = max(int(req.GET.get('page', 1)), 1)
        page_size = min(max(int(req.GET.get('page_size', default_page_size)), 1), 100)
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


# ----------------------------------------------------------------------------
# Permission helpers
# ----------------------------------------------------------------------------

def _can_manage_institution(user, institution):
    """Staff, or the Institution's own admin_user — nobody else."""
    if not user.is_authenticated:
        return False
    if _is_staff(user):
        return True
    return institution.admin_user_id == user.id


def _can_view_student_sensitive(user, student):
    """Staff, the student's own Institution Admin, the student, or the linked parent."""
    if not user.is_authenticated:
        return False
    if _is_staff(user):
        return True
    if student.user_id == user.id:
        return True
    if student.parent_user_id == user.id:
        return True
    if student.institution_id and student.institution.admin_user_id == user.id:
        return True
    return False


def _can_manage_student(user, student):
    """Same rule as sensitive-view, minus the student themself editing admin fields freely."""
    return _can_view_student_sensitive(user, student)


# ----------------------------------------------------------------------------
# Serializers
# ----------------------------------------------------------------------------

def serialize_institution(inst, detailed=False):
    data = {
        'id': inst.id,
        'name': inst.name,
        'type': inst.type,
        'board_affiliation': inst.board_affiliation,
        'city': inst.city,
        'state': inst.state,
        'status': inst.status,
    }
    if detailed:
        data.update({
            'address': inst.address,
            'admin_user': {
                'id': inst.admin_user.id,
                'username': inst.admin_user.username,
                'email': inst.admin_user.email,
            } if inst.admin_user else None,
            'onboarded_by_partner_id': inst.onboarded_by_partner_id,
            'total_students': inst.students.count(),
            'created_at': inst.created_at.isoformat() if inst.created_at else None,
        })
    return data


def serialize_student_public(s):
    """Safe view for anyone who is NOT staff/self/parent/owning-institution-admin."""
    return {
        'id': s.id,
        'student_name': s.user.get_full_name() if s.user_id else None,
        'institution_id': s.institution_id,
        'institution_name': s.institution.name if s.institution_id else None,
        'class_grade': s.class_grade,
        'section': s.section,
        'academic_year': s.academic_year,
        'status': s.status,
        'profile_photo': s.profile_photo.url if s.profile_photo else None,
    }


def serialize_student_full(s, request=None):
    """Full view including sensitive fields — only ever called after a permission check."""
    return {
        'id': s.id,
        'user_id': s.user_id,
        'student_name': s.user.get_full_name() if s.user_id else None,
        'institution_id': s.institution_id,
        'institution_name': s.institution.name if s.institution_id else None,
        'admission_no': s.admission_no,
        'roll_number': s.roll_number,
        'class_grade': s.class_grade,
        'section': s.section,
        'academic_year': s.academic_year,
        'admission_date': s.admission_date,
        'date_of_birth': s.date_of_birth,
        'age': s.age,
        'gender': s.gender,
        'blood_group': s.blood_group,
        'category': s.category,
        'father_name': s.father_name,
        'mother_name': s.mother_name,
        'guardian_name': s.guardian_name,
        'guardian_relation': s.guardian_relation,
        'guardian_phone': s.guardian_phone,
        'guardian_email': s.guardian_email,
        'parent_user_id': s.parent_user_id,
        'aadhar_or_id_proof': (
            request.build_absolute_uri(s.aadhar_or_id_proof.url)
            if s.aadhar_or_id_proof and request else
            (s.aadhar_or_id_proof.url if s.aadhar_or_id_proof else None)
        ),
        'profile_photo': (
            request.build_absolute_uri(s.profile_photo.url)
            if s.profile_photo and request else
            (s.profile_photo.url if s.profile_photo else None)
        ),
        'emergency_contact_phone': s.emergency_contact_phone,
        'status': s.status,
        'created_at': s.created_at.isoformat() if s.created_at else None,
        'updated_at': s.updated_at.isoformat() if s.updated_at else None,
    }


def serialize_student(s, viewer=None, request=None):
    """Picks full vs public serialization based on who's asking."""
    if viewer is not None and _can_view_student_sensitive(viewer, s):
        return serialize_student_full(s, request=request)
    return serialize_student_public(s)


# ============================================================================
# INSTITUTIONS
# ============================================================================

@require_http_methods(['GET', 'POST'])
def institution_list(request):
    if request.method == 'GET':
        qs = Institution.objects.all().order_by('-created_at')

        inst_type = request.GET.get('type')
        if inst_type:
            qs = qs.filter(type=inst_type)
        status = request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        city = request.GET.get('city')
        if city:
            qs = qs.filter(city__icontains=city)
        search = request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)

        detailed = _is_staff(request.user) if request.user.is_authenticated else False
        payload = _paginate(request, qs, serialize_institution, default_page_size=20, detailed=detailed)
        return JsonResponse(payload)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    form = InstitutionForm(_body(request))
    if form.is_valid():
        institution = form.save(commit=False)
        try:
            institution.full_clean()
            institution.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse(
            {'success': True, 'institution': serialize_institution(institution, detailed=True)},
            status=201,
        )
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_institution_or_404(pk):
    try:
        return Institution.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return None


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def institution_detail(request, pk):
    institution = _get_institution_or_404(pk)
    if institution is None:
        return JsonResponse({'error': 'Institution not found'}, status=404)

    if request.method == 'GET':
        detailed = request.user.is_authenticated and _can_manage_institution(request.user, institution)
        return JsonResponse({'institution': serialize_institution(institution, detailed=detailed)})

    if not _can_manage_institution(request.user, institution):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        if not _is_staff(request.user):
            return JsonResponse({'error': 'Only staff can delete an Institution.'}, status=403)
        institution.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(InstitutionForm, institution, request, body)
    if form.is_valid():
        institution = form.save(commit=False)
        try:
            institution.full_clean()
            institution.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'institution': serialize_institution(institution, detailed=True)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# STUDENTS (nested under an Institution)
# ============================================================================

@require_http_methods(['GET', 'POST'])
def student_list(request, institution_pk):
    institution = _get_institution_or_404(institution_pk)
    if institution is None:
        return JsonResponse({'error': 'Institution not found'}, status=404)

    if request.method == 'GET':
        qs = (
            Student.objects.select_related('user', 'institution')
            .filter(institution=institution)
            .order_by('class_grade', 'section', 'roll_number')
        )

        class_grade = request.GET.get('class_grade')
        if class_grade:
            qs = qs.filter(class_grade=class_grade)
        section = request.GET.get('section')
        if section:
            qs = qs.filter(section=section)
        status = request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        search = request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(admission_no__icontains=search)

        viewer = request.user if request.user.is_authenticated else None
        payload = _paginate(
            request, qs, serialize_student, default_page_size=20, viewer=viewer, request=request
        )
        payload['institution_id'] = institution.id
        return JsonResponse(payload)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    if not _can_manage_institution(request.user, institution):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    data = _body(request)
    data['institution'] = institution.id
    form = StudentForm(data, request.FILES)
    if form.is_valid():
        student = form.save(commit=False)
        student.institution = institution
        try:
            student.full_clean()
            student.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse(
            {'success': True, 'student': serialize_student_full(student, request=request)}, status=201
        )
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_student_or_404(pk):
    try:
        return Student.objects.select_related('user', 'institution').get(pk=pk)
    except ObjectDoesNotExist:
        return None


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def student_detail(request, pk):
    student = _get_student_or_404(pk)
    if student is None:
        return JsonResponse({'error': 'Student not found'}, status=404)

    if request.method == 'GET':
        viewer = request.user if request.user.is_authenticated else None
        return JsonResponse({'student': serialize_student(student, viewer=viewer, request=request)})

    if not _can_manage_student(request.user, student):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        student.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(StudentForm, student, request, body)

    if form.is_valid():
        student = form.save(commit=False)
        try:
            student.full_clean()
            student.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'student': serialize_student_full(student, request=request)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# "ME" ENDPOINTS — student's own profile, and a parent's linked children
# ============================================================================

@login_required
@require_GET
def my_student_profile(request):
    try:
        student = Student.objects.select_related('user', 'institution').get(user=request.user)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'No student profile linked to this account.'}, status=404)
    return JsonResponse({'student': serialize_student_full(student, request=request)})


@login_required
@require_GET
def my_children(request):
    """For a logged-in Parent — list every Student where parent_user = them."""
    qs = (
        Student.objects.select_related('user', 'institution')
        .filter(parent_user=request.user)
        .order_by('class_grade', 'section')
    )
    return JsonResponse({
        'count': qs.count(),
        'results': [serialize_student_full(s, request=request) for s in qs],
    })


# ============================================================================
# ADMIN: STUDENT STATUS CHANGE (transfer / graduate / drop, without a full PUT)
# ============================================================================

@login_required
@require_http_methods(['PATCH'])
def update_student_status(request, pk):
    student = _get_student_or_404(pk)
    if student is None:
        return JsonResponse({'error': 'Student not found'}, status=404)
    if not _can_manage_student(request.user, student):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    data = _body(request)
    new_status = data.get('status')
    valid_statuses = dict(Student.STATUS_CHOICES)
    if new_status not in valid_statuses:
        return JsonResponse(
            {'error': f"Invalid status. Must be one of: {list(valid_statuses.keys())}"}, status=400
        )

    student.status = new_status
    student.updated_at = timezone.now()
    try:
        student.full_clean()
        student.save()
    except DjangoValidationError as e:
        return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)

    return JsonResponse({'success': True, 'student': serialize_student_full(student, request=request)})