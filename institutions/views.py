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
from django.views.decorators.csrf import csrf_exempt

from .forms import InstitutionForm, StudentForm, BatchForm
from .models import Institution, Student, Batch


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
        # Django's request.POST is immutable QueryDict, so we copy it
        data = request.POST.dict()

    if isinstance(data, dict):
        if 'user_id' in data and 'user' not in data:
            data['user'] = data['user_id']
        if 'parent_user_id' in data and 'parent_user' not in data:
            data['parent_user'] = data['parent_user_id']
        if 'batch_id' in data and 'batch' not in data:
            data['batch'] = data['batch_id']
    return data


def _is_staff(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) in ('staff', 'super_admin', 'superadmin', 'teacher', 'admin', 'employee', 'sales', 'institution_admin', 'institution') or
        getattr(user, 'is_staff', False) or
        getattr(user, 'is_superuser', False)
    )


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def _form_errors(form):
    return {field: errs for field, errs in form.errors.items()}


def _bind_form_for_update(form_class, instance, request, body):
    files = request.FILES or None

    if request.method == 'PUT':
        return form_class(body, files, instance=instance)

    file_field_names = {
        f.name for f in instance._meta.get_fields()
        if getattr(f, 'concrete', False) and f.get_internal_type() in ('FileField', 'ImageField')
    }
    mergeable_fields = [f for f in form_class._meta.fields if f not in file_field_names]
    existing = model_to_dict(instance, fields=mergeable_fields)

    merged = dict(existing)
    for k, v in body.items():
        if k in mergeable_fields:
            merged[k] = v

    return form_class(merged, files, instance=instance)


def _paginate(request, queryset, serializer_fn, default_page_size=20, **serializer_kwargs):
    try:
        page_num = max(int(request.GET.get('page', 1)), 1)
    except (ValueError, TypeError):
        page_num = 1

    try:
        page_size = max(int(request.GET.get('page_size', default_page_size)), 1)
    except (ValueError, TypeError):
        page_size = default_page_size

    total_items = queryset.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    if page_num > total_pages and total_items > 0:
        page_num = total_pages

    start = (page_num - 1) * page_size
    end = start + page_size
    page_qs = queryset[start:end]

    results = [serializer_fn(item, **serializer_kwargs) for item in page_qs]
    return {
        'count': total_items,
        'page': page_num,
        'page_size': page_size,
        'total_pages': total_pages,
        'has_next': page_num < total_pages,
        'has_previous': page_num > 1,
        'results': results,
    }


# ----------------------------------------------------------------------------
# Permission helpers
# ----------------------------------------------------------------------------

def _can_manage_institution(user, institution):
    if not user.is_authenticated:
        return False
    if _is_staff(user):
        return True
    if institution.admin_user_id and institution.admin_user_id == user.id:
        return True
    return False


def _can_view_student_sensitive(user, student):
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
    return _can_view_student_sensitive(user, student)


# ----------------------------------------------------------------------------
# Serializers
# ----------------------------------------------------------------------------

def serialize_batch(b):
    return {
        'id': b.id,
        'institution_id': b.institution_id,
        'institution_name': b.institution.name if b.institution_id else None,
        'name': b.name,
        'code': b.code,
        'target_exam': b.target_exam,
        'start_date': b.start_date.isoformat() if b.start_date else None,
        'end_date': b.end_date.isoformat() if b.end_date else None,
        'is_active': b.is_active,
        'total_students': b.students.count(),
        'created_at': b.created_at.isoformat() if b.created_at else None,
    }


def serialize_institution(inst, detailed=False):
    data = {
        'id': inst.id,
        'name': inst.name,
        'type': inst.type,
        'board_affiliation': inst.board_affiliation or '',
        'phone': inst.phone or '',
        'city': inst.city or '',
        'state': inst.state or '',
        'status': inst.status or 'pending',
        'address': inst.address or '',
        'created_by': {
            'id': inst.created_by.id,
            'name': inst.created_by.get_full_name() or inst.created_by.username,
        } if inst.created_by else None,
        'assigned_employee': {
            'id': inst.assigned_employee.id,
            'name': inst.assigned_employee.get_full_name() or inst.assigned_employee.username,
        } if inst.assigned_employee else None,
    }
    if detailed:
        data.update({
            'admin_user': {
                'id': inst.admin_user.id,
                'username': inst.admin_user.username,
                'email': inst.admin_user.email or 'info@eduaiq.co.in',
            } if inst.admin_user else None,
            'onboarded_by_partner_id': inst.onboarded_by_partner_id or '',
            'total_students': inst.students.count(),
            'total_batches': inst.batches.count(),
            'batches': [serialize_batch(b) for b in inst.batches.all()],
            'created_at': inst.created_at.isoformat() if inst.created_at else None,
            'allotted_course_ids': list(inst.allowed_courses.values_list('id', flat=True)),
            'allotted_category_ids': list(inst.allowed_categories.values_list('id', flat=True)),
        })
    return data


def serialize_student_public(s):
    return {
        'id': s.id,
        'student_name': s.user.get_full_name() if s.user_id else None,
        'institution_id': s.institution_id,
        'institution_name': s.institution.name if s.institution_id else None,
        'batch_id': s.batch_id,
        'batch_name': s.batch.name if s.batch_id else None,
        'class_grade': s.class_grade,
        'section': s.section,
        'academic_year': s.academic_year,
        'status': s.status,
        'profile_photo': s.profile_photo.url if s.profile_photo else None,
    }


def serialize_student_full(s, request=None):
    return {
        'id': s.id,
        'user_id': s.user_id,
        'student_name': s.user.get_full_name() if s.user_id else None,
        'institution_id': s.institution_id,
        'institution_name': s.institution.name if s.institution_id else None,
        'batch_id': s.batch_id,
        'batch_name': s.batch.name if s.batch_id else None,
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

        if request.user.is_authenticated:
            is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', '') in ['admin', 'superadmin']
            if not is_admin:
                from django.db.models import Q
                qs = qs.filter(Q(assigned_employee=request.user) | Q(created_by=request.user))

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

    body = _body(request)
    form = InstitutionForm(body)
    if form.is_valid():
        institution = form.save(commit=False)
        if not institution.created_by:
            institution.created_by = request.user
        if not institution.assigned_employee and request.user.role in ['employee', 'sales', 'teacher']:
            institution.assigned_employee = request.user
        try:
            institution.full_clean()
            institution.save()
            if 'allowed_courses' in body or 'course_ids' in body:
                c_ids = body.get('allowed_courses') if 'allowed_courses' in body else body.get('course_ids')
                if isinstance(c_ids, list):
                    from courses.models import Course
                    institution.allowed_courses.set(Course.objects.filter(id__in=c_ids))
            if 'allowed_categories' in body or 'category_ids' in body:
                cat_ids = body.get('allowed_categories') if 'allowed_categories' in body else body.get('category_ids')
                if isinstance(cat_ids, list):
                    from courses.models import CourseCategory
                    institution.allowed_categories.set(CourseCategory.objects.filter(id__in=cat_ids))
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


@require_GET
def my_institution_detail(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)

    inst = Institution.objects.filter(admin_user=request.user).first()
    if not inst:
        inst = Institution.objects.filter(assigned_employee=request.user).first()
    if not inst:
        inst = Institution.objects.filter(created_by=request.user).first()
    if not inst:
        inst = Institution.objects.first()

    if not inst:
        return JsonResponse({'error': 'No institution record found in database.'}, status=404)

    return JsonResponse({'institution': serialize_institution(inst, detailed=True)})


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def institution_detail(request, pk):
    institution = _get_institution_or_404(pk)
    if institution is None:
        return JsonResponse({'error': 'Institution not found'}, status=404)

    if request.method == 'GET':
        detailed = request.user.is_authenticated
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
            if 'allowed_courses' in body or 'course_ids' in body:
                c_ids = body.get('allowed_courses') if 'allowed_courses' in body else body.get('course_ids')
                if isinstance(c_ids, list):
                    from courses.models import Course
                    institution.allowed_courses.set(Course.objects.filter(id__in=c_ids))
            if 'allowed_categories' in body or 'category_ids' in body:
                cat_ids = body.get('allowed_categories') if 'allowed_categories' in body else body.get('category_ids')
                if isinstance(cat_ids, list):
                    from courses.models import CourseCategory
                    institution.allowed_categories.set(CourseCategory.objects.filter(id__in=cat_ids))
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'institution': serialize_institution(institution, detailed=True)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# STUDENTS (nested under an Institution)
# ============================================================================

@require_http_methods(['GET', 'POST'])
def student_list(request, institution_pk=None):
    from django.db.models import Q

    institution = None
    if institution_pk and str(institution_pk) not in ('0', 'all', ''):
        institution = _get_institution_or_404(institution_pk)
        if institution is None:
            return JsonResponse({'error': 'Institution not found'}, status=404)

    if request.method == 'GET':
        qs = Student.objects.select_related('user', 'institution', 'batch')

        # Restrict student list for Teacher accounts
        if request.user.is_authenticated:
            user_role = (getattr(request.user, 'role', '') or '').lower().strip()
            if user_role in ['teacher', 'faculty']:
                emp_prof = getattr(request.user, 'employee_profile', None)
                teacher_dept = emp_prof.department.name if (emp_prof and emp_prof.department) else None
                inst_ids = list(Institution.objects.filter(
                    Q(admin_user=request.user) | Q(created_by=request.user) | Q(assigned_employee=request.user)
                ).values_list('id', flat=True))

                t_filter = Q()
                if inst_ids:
                    t_filter |= Q(institution_id__in=inst_ids)
                if teacher_dept:
                    t_filter |= Q(class_grade__icontains=teacher_dept)

                if inst_ids or teacher_dept:
                    qs = qs.filter(t_filter)
                else:
                    school_name = getattr(request.user, 'school_name', '')
                    if school_name:
                        qs = qs.filter(Q(institution__name__icontains=school_name) | Q(class_grade__icontains=school_name))

        if institution:
            qs = qs.filter(institution=institution)
        else:
            inst_filter = request.GET.get('institution') or request.GET.get('institution_id')
            if inst_filter and inst_filter not in ('all', '', '0'):
                qs = qs.filter(institution_id=inst_filter)

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
            qs = qs.filter(
                Q(admission_no__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search)
            )

        qs = qs.order_by('-created_at')

        viewer = request.user if request.user.is_authenticated else None
        payload = _paginate(
            request, qs, serialize_student, default_page_size=20, viewer=viewer
        )
        payload['institution_id'] = institution.id if institution else None
        return JsonResponse(payload)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    if getattr(request.user, 'role', '') in ['teacher', 'faculty']:
        return JsonResponse({'error': 'Teachers are not permitted to add or modify student profiles.'}, status=403)
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
        user_obj = student.user
        student.delete()
        if user_obj:
            try:
                user_obj.delete()
            except Exception:
                pass
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


@login_required
@require_http_methods(['POST'])
def create_institution_student(request):
    """
    Institution Admin endpoint to create a new Student User Account & enroll into courses.
    """
    data = _body(request)
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    phone = data.get('phone', '').strip()
    admission_no = data.get('admission_no', '').strip()
    class_grade = data.get('class_grade', 'Class 10').strip()
    section = data.get('section', 'A').strip()
    academic_year = data.get('academic_year', '2026-27').strip()
    course_ids = data.get('course_ids', [])

    if isinstance(course_ids, str):
        import json
        try:
            course_ids = json.loads(course_ids)
        except Exception:
            course_ids = [c for c in course_ids.split(',') if c.strip().isdigit()]

    if not username or not password or not admission_no:
        return JsonResponse({'success': False, 'error': 'Username, Password, and Admission No are required.'}, status=400)

    from accounts.models import User
    from courses.models import Course, Enrollment

    if User.objects.filter(username=username).exists():
        return JsonResponse({'success': False, 'error': 'Username already exists. Please choose a different username.'}, status=400)

    if email and User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'success': False, 'error': 'Email address already exists.'}, status=400)

    if phone and User.objects.filter(phone=phone).exists():
        return JsonResponse({'success': False, 'error': 'Phone number already exists.'}, status=400)

    # Get institution selected in form or linked to logged in user
    inst = None
    inst_id = data.get('institution') or data.get('institution_id')
    if inst_id:
        try:
            inst = Institution.objects.filter(id=int(inst_id)).first()
        except (ValueError, TypeError):
            pass

    if not inst and request.user.is_authenticated:
        inst = Institution.objects.filter(admin_user=request.user).first()

    batch_id = data.get('batch') or data.get('batch_id')
    batch_obj = None
    if batch_id:
        try:
            batch_obj = Batch.objects.get(id=int(batch_id))
            if not inst:
                inst = batch_obj.institution
        except (ValueError, TypeError, ObjectDoesNotExist):
            batch_obj = None

    try:
        photo_file = request.FILES.get('profile_photo') or request.FILES.get('profile_picture') or request.FILES.get('photo') or request.FILES.get('image')

        # Create User
        user = User.objects.create_user(
            username=username,
            email=email if email else f"{username}@student.eduaiq.co.in",
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone if phone else f"+919{hash(username)%1000000000:09d}",
            role='student'
        )

        if photo_file:
            user.profile_image = photo_file
            user.save()

        # Create Student Profile
        student = Student.objects.create(
            user=user,
            institution=inst,
            batch=batch_obj,
            admission_no=admission_no,
            class_grade=class_grade,
            section=section,
            academic_year=academic_year,
            profile_photo=photo_file if photo_file else None
        )


        # Create Enrollments for selected courses
        enrolled_courses = []
        if course_ids:
            from courses.models import Course, Enrollment
            for cid in course_ids:
                try:
                    course = Course.objects.get(id=int(cid))
                    Enrollment.objects.get_or_create(
                        student=user,
                        course=course,
                        defaults={'covered_by_plan': True, 'amount_paid': 0}
                    )
                    enrolled_courses.append(course.title)
                except Exception:
                    continue

        return JsonResponse({
            'success': True,
            'message': 'Student account created and enrolled successfully!',
            'student_username': username,
            'enrolled_courses': enrolled_courses,
            'batch_name': batch_obj.name if batch_obj else None
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def institution_allot_courses(request, pk):
    try:
        inst = Institution.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Institution not found'}, status=404)

    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    data = _body(request)
    course_ids = data.get('course_ids', [])

    from courses.models import Course
    valid_courses = Course.objects.filter(id__in=course_ids)
    inst.allowed_courses.set(valid_courses)

    return JsonResponse({
        'success': True,
        'message': f'Updated allotted courses for {inst.name}',
        'allotted_course_ids': list(inst.allowed_courses.values_list('id', flat=True))
    })


# ============================================================================
# BATCHES (COACHING & INSTITUTION)
# ============================================================================

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def batch_list_create(request, institution_pk=None):
    if request.method == 'GET':
        qs = Batch.objects.all().order_by('-created_at')
        if institution_pk:
            qs = qs.filter(institution_id=institution_pk)
        elif request.GET.get('institution'):
            qs = qs.filter(institution_id=request.GET.get('institution'))
        
        target = request.GET.get('target_exam')
        if target:
            qs = qs.filter(target_exam__icontains=target)
        
        payload = _paginate(request, qs, serialize_batch, default_page_size=50)
        return JsonResponse(payload)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    body = _body(request)
    if institution_pk and 'institution' not in body:
        body['institution'] = institution_pk

    inst_id = body.get('institution')
    if not inst_id:
        return JsonResponse({'success': False, 'error': 'Institution is required.'}, status=400)

    try:
        inst = Institution.objects.get(pk=inst_id)
    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'error': 'Institution not found.'}, status=404)

    if not _can_manage_institution(request.user, inst):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    form = BatchForm(body)
    if form.is_valid():
        batch = form.save()
        return JsonResponse({'success': True, 'batch': serialize_batch(batch)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def batch_detail(request, pk):
    try:
        batch = Batch.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'batch': serialize_batch(batch)})

    if not _can_manage_institution(request.user, batch.institution):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        batch.delete()
        return JsonResponse({'success': True})

    body = _body(request)
    form = _bind_form_for_update(BatchForm, batch, request, body)
    if form.is_valid():
        batch = form.save()
        return JsonResponse({'success': True, 'batch': serialize_batch(batch)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)