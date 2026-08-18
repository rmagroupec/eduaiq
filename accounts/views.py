"""
Account Views — Pure JSON API
No template rendering. Every view returns JsonResponse.
Consumed via fetch()/AJAX from your own frontend.
"""

import json

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from .forms import DeleteAccountForm, ProfileForm, SignUpForm, UserEditForm
from .models import Profile, Role, User


# ============================================================================
# HELPERS
# ============================================================================

def _body(request):
    """Parse JSON body; falls back to POST data for form-encoded requests."""
    if request.body:
        try:
            return json.loads(request.body)
        except (ValueError, TypeError):
            pass
    return request.POST.dict()


def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email or 'info@eduaiq.co.in',
        'phone': getattr(user, 'phone', None) or '+91 8052350041',
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile_image': user.profile_image.url if user.profile_image else None,
        'date_of_birth': user.date_of_birth,
        'gender': user.gender,
        'caste_category': user.caste_category,
        'marital_status': user.marital_status,
        'father_name': user.father_name,
        'mother_name': user.mother_name,
        'role': user.role,
        'qualification': user.qualification,
        'experience': user.experience,
        'contract_type': user.contract_type,
        'shift': user.shift,
        'joining_date': user.joining_date,
        'school_name': user.school_name,
        'academic_year': user.academic_year,
        'facebook': user.facebook,
        'instagram': user.instagram,
        'linkedin': user.linkedin,
        'description': user.description,
        'is_verified': user.is_verified,
        'status': user.status,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
    }


def serialize_profile(profile):
    return {
        'user_id': profile.user_id,
        'address': profile.address,
        'city': profile.city,
        'state': profile.state,
        'pincode': profile.pincode,
    }


def serialize_role(role):
    return {'id': role.id, 'name': role.name}


def _is_staff(user):
    return user.is_authenticated and (
        user.is_staff or 
        user.is_superuser or 
        getattr(user, 'role', None) in ('staff', 'super_admin', 'teacher', 'admin')
    )


# ============================================================================
# AUTHENTICATION
# ============================================================================

@csrf_exempt
@require_http_methods(['POST'])
def signup(request):
    data = _body(request)
    form = SignUpForm(data)
    if form.is_valid():
        user = form.save()
        Profile.objects.get_or_create(user=user)
        login(request, user)
        return JsonResponse({'success': True, 'user': serialize_user(user)}, status=201)
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@csrf_exempt
@require_http_methods(['POST'])
def login_view(request):
    data = _body(request)
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return JsonResponse({'success': False, 'error': 'username and password are required'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

    login(request, user)
    return JsonResponse({'success': True, 'user': serialize_user(user)})


@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    return JsonResponse({'success': True})


# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

@login_required
@require_http_methods(['POST'])
def change_password(request):
    data = _body(request)
    form = PasswordChangeForm(user=request.user, data={
        'old_password': data.get('old_password', ''),
        'new_password1': data.get('new_password1', ''),
        'new_password2': data.get('new_password2', ''),
    })
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_http_methods(['POST'])
def delete_account(request):
    data = _body(request)
    form = DeleteAccountForm(data, user=request.user)
    if form.is_valid():
        user = request.user
        logout(request)
        user.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================================
# USER PROFILE
# ============================================================================

@ensure_csrf_cookie
@login_required
@require_GET
def user_profile(request):
    # ensure_csrf_cookie guarantees a csrftoken cookie is set here, so this
    # endpoint doubles as the way to obtain a CSRF token (after login) for
    # the other protected POST/PUT endpoints below.
    return JsonResponse({'user': serialize_user(request.user)})


@login_required
@require_http_methods(['PUT', 'PATCH', 'POST'])
def user_edit(request):
    data = _body(request)
    form = UserEditForm(data, instance=request.user)
    if form.is_valid():
        user = form.save()
        return JsonResponse({'success': True, 'user': serialize_user(user)})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_GET
def profile_detail(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return JsonResponse({'profile': serialize_profile(profile)})


@login_required
@require_http_methods(['PUT', 'PATCH', 'POST'])
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    data = _body(request)
    form = ProfileForm(data, instance=profile)
    if form.is_valid():
        profile = form.save()
        return JsonResponse({'success': True, 'profile': serialize_profile(profile)})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================================
# USER MANAGEMENT (Admin/Staff)
# ============================================================================

@login_required
@require_GET
def user_list(request):
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    qs = User.objects.all().order_by('-created_at')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )
    role = request.GET.get('role')
    if role:
        qs = qs.filter(role=role)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    exclude_has_profile = request.GET.get('exclude_has_profile')
    if exclude_has_profile == 'true':
        qs = qs.filter(student_profile__isnull=True)

    try:
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(max(int(request.GET.get('page_size', 25)), 1), 100)
    except ValueError:
        page, page_size = 1, 25

    total = qs.count()
    start = (page - 1) * page_size
    users = qs[start:start + page_size]

    return JsonResponse({
        'count': total,
        'page': page,
        'page_size': page_size,
        'results': [serialize_user(u) for u in users],
    })


@login_required
@require_GET
def user_detail(request, pk):
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        user = User.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    return JsonResponse({'user': serialize_user(user)})


# ============================================================================
# ROLE MANAGEMENT (Admin/Staff)
# ============================================================================

@login_required
@require_GET
def role_list(request):
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    roles = Role.objects.all().order_by('name')
    return JsonResponse({'results': [serialize_role(r) for r in roles]})


# ============================================================================
# API (JSON/AJAX) — availability checks + stats
# ============================================================================

@require_GET
def check_username(request):
    username = request.GET.get('username', '').strip()
    if not username:
        return JsonResponse({'available': False, 'error': 'username is required'}, status=400)
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'username': username, 'available': not exists})


@require_GET
def check_email(request):
    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'available': False, 'error': 'email is required'}, status=400)
    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({'email': email, 'available': not exists})


@require_GET
def check_phone(request):
    phone = request.GET.get('phone', '').strip()
    if not phone:
        return JsonResponse({'available': False, 'error': 'phone is required'}, status=400)
    exists = User.objects.filter(phone=phone).exists()
    return JsonResponse({'phone': phone, 'available': not exists})


@login_required
@require_GET
def user_stats(request):
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    total_users = User.objects.count()
    active_users = User.objects.filter(status=User.StatusChoices.ACTIVE).count()
    inactive_users = User.objects.filter(status=User.StatusChoices.INACTIVE).count()
    verified_users = User.objects.filter(is_verified=True).count()
    by_role = list(User.objects.values('role').annotate(count=Count('id')).order_by('-count'))
    by_gender = list(User.objects.values('gender').annotate(count=Count('id')).order_by('-count'))

    return JsonResponse({
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'verified_users': verified_users,
        'by_role': by_role,
        'by_gender': by_gender,
    })


# ============================================================================
# DEPARTMENT, DESIGNATION & EMPLOYEE ONBOARDING APIS
# ============================================================================

from .models import Department, Designation, EmployeeProfile, EmployeeDocument, OnboardingTask

@login_required
def department_api(request):
    """API for listing and creating Departments"""
    if request.method == 'GET':
        depts = list(Department.objects.all().values('id', 'name', 'code', 'description', 'is_active', 'created_at'))
        return JsonResponse({'status': 'success', 'data': depts})
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            name = data.get('name')
            code = data.get('code')
            description = data.get('description', '')
            if not name or not code:
                return JsonResponse({'status': 'error', 'message': 'Name and Code are required.'}, status=400)
            
            dept, created = Department.objects.get_or_create(code=code, defaults={'name': name, 'description': description})
            if not created:
                dept.name = name
                dept.description = description
                dept.save()
            return JsonResponse({'status': 'success', 'message': 'Department saved successfully.', 'id': dept.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def designation_api(request):
    """API for listing and creating Designations"""
    if request.method == 'GET':
        desigs = Designation.objects.select_related('department')
        data = [{'id': d.id, 'title': d.title, 'department_id': d.department_id, 'department_name': d.department.name} for d in desigs]
        return JsonResponse({'status': 'success', 'data': data})
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            title = data.get('title')
            department_id = data.get('department_id')
            description = data.get('description', '')
            if not title or not department_id:
                return JsonResponse({'status': 'error', 'message': 'Title and Department ID are required.'}, status=400)
            
            desig = Designation.objects.create(title=title, department_id=department_id, description=description)
            return JsonResponse({'status': 'success', 'message': 'Designation created successfully.', 'id': desig.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def employee_onboarding_api(request):
    """API for onboarding a new employee and viewing employee profiles"""
    if request.method == 'GET':
        employees = EmployeeProfile.objects.select_related('user', 'department', 'designation').prefetch_related('documents')
        data = []
        for emp in employees:
            data.append({
                'id': emp.id,
                'employee_id': emp.employee_id,
                'full_name': emp.user.get_full_name() or emp.user.username,
                'email': emp.user.email,
                'phone': emp.user.phone,
                'role': emp.user.role,
                'department': emp.department.name if emp.department else 'N/A',
                'designation': emp.designation.title if emp.designation else 'N/A',
                'joining_date': emp.joining_date.strftime('%Y-%m-%d') if emp.joining_date else 'N/A',
                'onboarding_status': emp.onboarding_status,
                'onboarding_status_display': emp.get_onboarding_status_display(),
                'docs_count': emp.documents.count(),
            })
        return JsonResponse({'status': 'success', 'data': data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            email = data.get('email', '').strip()
            phone = data.get('phone', '').strip()
            role = data.get('role', 'employee')
            department_id = data.get('department_id')
            designation_id = data.get('designation_id')
            joining_date = data.get('joining_date')
            
            if not email or not first_name:
                return JsonResponse({'status': 'error', 'message': 'First name and Email are required.'}, status=400)

            username = email.split('@')[0] + "_" + phone[-4:] if phone else email.split('@')[0]
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone or f"+9199{User.objects.count():08d}",
                    'role': role,
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                user.set_password('EduAiQ@123')
                user.save()

            emp_id = f"EMP-{user.id:04d}"
            emp_profile, _ = EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': emp_id,
                    'department_id': department_id,
                    'designation_id': designation_id,
                    'joining_date': joining_date,
                    'onboarding_status': 'under_review'
                }
            )

            # Assign default checklist tasks
            default_tasks = ["ID Proof Submitted", "Work Email Created", "System Allocated", "HR Agreement Signed"]
            for task in default_tasks:
                OnboardingTask.objects.get_or_create(employee=emp_profile, title=task)

            return JsonResponse({'status': 'success', 'message': 'Employee onboarded successfully!', 'employee_id': emp_id, 'user_id': user.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


from .models import Attendance
from datetime import datetime

@csrf_exempt
def attendance_api(request):
    """
    API endpoint for getting and updating User Attendance.
    GET: Returns formatted monthly attendance matrix for a user.
    POST: Save or update attendance records for a user.
    """
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        user_name = request.GET.get('username') or request.GET.get('user_name') or request.GET.get('email')
        academic_year = request.GET.get('academic_year', 'Jun 2025/2026')

        user = None
        if user_id:
            user = User.objects.filter(id=user_id).first()
        elif user_name:
            user = User.objects.filter(
                Q(username__iexact=user_name) | 
                Q(email__iexact=user_name) | 
                Q(first_name__icontains=user_name.split()[0])
            ).first()
        elif request.user.is_authenticated:
            user = request.user

        month_map = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }

        if not user:
            matrix = {month_name: {} for month_name in month_map.values()}
            return JsonResponse({'status': 'success', 'attendance_matrix': matrix, 'message': 'No user found'})

        records = Attendance.objects.filter(user=user)
        if academic_year:
            records = records.filter(academic_year=academic_year)

        month_map = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }

        # Initialize matrix for 12 months
        matrix = {month_name: {} for month_name in month_map.values()}

        for rec in records:
            m_name = month_map.get(rec.date.month)
            if m_name:
                matrix[m_name][rec.date.day] = rec.status

        return JsonResponse({
            'status': 'success',
            'user_id': user.id,
            'user_name': user.get_full_name() or user.username,
            'academic_year': academic_year,
            'attendance_matrix': matrix
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            user_id = data.get('user_id')
            date_str = data.get('date') # YYYY-MM-DD
            status = data.get('status', 'P').upper()
            academic_year = data.get('academic_year', 'Jun 2025/2026')
            remarks = data.get('remarks', '')

            if not user_id or not date_str:
                return JsonResponse({'status': 'error', 'message': 'user_id and date are required'}, status=400)

            att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            user = User.objects.get(id=user_id)

            att, created = Attendance.objects.update_or_create(
                user=user,
                date=att_date,
                defaults={
                    'status': status,
                    'academic_year': academic_year,
                    'remarks': remarks
                }
            )

            return JsonResponse({
                'status': 'success',
                'message': f'Attendance for {user.username} on {date_str} saved successfully.',
                'attendance_id': att.id
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def attendance_check_in_api(request):
    """API for Employee Self Punch-In / Check-In"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)
    
    user = request.user if request.user.is_authenticated else User.objects.first()
    if not user:
        return JsonResponse({'status': 'error', 'message': 'No user authenticated'}, status=401)
    
    today = datetime.now().date()
    now_time = datetime.now().time()
    
    # Auto-detect status: Present ('P') or Late ('L') if after 09:30 AM
    late_cutoff = datetime.strptime('09:30:00', '%H:%M:%S').time()
    status = 'L' if now_time > late_cutoff else 'P'
    academic_year = 'Jun 2025/2026'

    att, created = Attendance.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'status': status,
            'check_in': now_time,
            'academic_year': academic_year,
            'remarks': 'Self Punch-In'
        }
    )

    if not created:
        if not att.check_in:
            att.check_in = now_time
            att.status = status
            att.save()
        return JsonResponse({
            'status': 'info',
            'message': f'Already checked in at {att.check_in.strftime("%I:%M %p")}',
            'check_in': att.check_in.strftime("%I:%M %p"),
            'attendance_status': att.status
        })

    return JsonResponse({
        'status': 'success',
        'message': f'Punch-In successful at {now_time.strftime("%I:%M %p")} ({att.get_status_display()})',
        'check_in': now_time.strftime("%I:%M %p"),
        'attendance_status': att.status
    })


@csrf_exempt
def attendance_check_out_api(request):
    """API for Employee Self Punch-Out / Check-Out"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)
    
    user = request.user if request.user.is_authenticated else User.objects.first()
    if not user:
        return JsonResponse({'status': 'error', 'message': 'No user authenticated'}, status=401)

    today = datetime.now().date()
    now_time = datetime.now().time()

    att = Attendance.objects.filter(user=user, date=today).first()
    if not att:
        # Create record if punch-out performed first
        att = Attendance.objects.create(
            user=user,
            date=today,
            status='P',
            check_out=now_time,
            academic_year='Jun 2025/2026',
            remarks='Direct Punch-Out'
        )
    else:
        att.check_out = now_time
        att.save()

    return JsonResponse({
        'status': 'success',
        'message': f'Punch-Out successful at {now_time.strftime("%I:%M %p")}',
        'check_out': now_time.strftime("%I:%M %p")
    })


@require_GET
def attendance_today_status_api(request):
    """API returning today's attendance state for active user"""
    user = request.user if request.user.is_authenticated else User.objects.first()
    if not user:
        return JsonResponse({'status': 'error', 'message': 'No user authenticated'}, status=401)

    today = datetime.now().date()
    att = Attendance.objects.filter(user=user, date=today).first()

    return JsonResponse({
        'status': 'success',
        'user_name': user.get_full_name() or user.username,
        'has_checked_in': bool(att and att.check_in),
        'has_checked_out': bool(att and att.check_out),
        'check_in_time': att.check_in.strftime("%I:%M %p") if att and att.check_in else None,
        'check_out_time': att.check_out.strftime("%I:%M %p") if att and att.check_out else None,
        'attendance_status': att.status if att else None
    })


from .models import WFHRequest
from datetime import timedelta

@csrf_exempt
def wfh_request_api(request):
    """
    API for Employee to apply for Work From Home (WFH) and view request status.
    GET: Returns list of WFH requests.
    POST: Submit a new WFH application (start_date, end_date, reason).
    """
    if request.method == 'GET':
        reqs = WFHRequest.objects.select_related('user', 'approved_by').order_by('-applied_at')
        user_id = request.GET.get('user_id')
        user_name = request.GET.get('user_name')
        email = request.GET.get('email')
        if user_id:
            reqs = reqs.filter(user_id=user_id)
        elif email:
            reqs = reqs.filter(
                Q(user__email__iexact=email) |
                Q(target_email__iexact=email)
            )
        elif user_name:
            reqs = reqs.filter(
                Q(user__first_name__icontains=user_name) |
                Q(user__last_name__icontains=user_name) |
                Q(user__username__icontains=user_name) |
                Q(target_name__icontains=user_name)
            )
        elif not _is_staff(request.user) and request.user.is_authenticated:
            reqs = reqs.filter(user=request.user)

        # Fallback: if filtering returned nothing for requested profile, return all recent requests
        if (email or user_name) and not reqs.exists():
            reqs = WFHRequest.objects.select_related('user', 'approved_by').order_by('-applied_at')

        data = []
        for r in reqs:
            data.append({
                'id': r.id,
                'user_id': r.user_id,
                'employee_name': r.target_name or (r.user.get_full_name() or r.user.username),
                'email': r.target_email or r.user.email,
                'role': r.user.role if hasattr(r.user, 'role') else 'Staff',
                'leave_type': getattr(r, 'leave_type', 'Work From Home (WFH)'),
                'start_date': r.start_date.strftime('%Y-%m-%d'),
                'end_date': r.end_date.strftime('%Y-%m-%d'),
                'reason': r.reason,
                'status': r.status,
                'status_display': r.get_status_display(),
                'applied_at': r.applied_at.strftime('%Y-%m-%d %H:%M'),
                'approved_by_name': (r.approved_by.get_full_name() or r.approved_by.username) if r.approved_by else None,
                'admin_remarks': r.admin_remarks
            })
        return JsonResponse({'status': 'success', 'data': data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            target_email = (data.get('email') or '').strip()
            target_name = (data.get('user_name') or '').strip()

            user = None
            if target_email:
                user = User.objects.filter(email__iexact=target_email).first()
            if not user and target_name:
                user = User.objects.filter(
                    Q(first_name__icontains=target_name) |
                    Q(last_name__icontains=target_name) |
                    Q(username__icontains=target_name)
                ).first()
            if not user:
                user = request.user if request.user.is_authenticated else User.objects.first()

            leave_type = data.get('leave_type', 'Work From Home (WFH)')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            reason = data.get('reason', '').strip()

            if not start_date_str or not end_date_str or not reason:
                return JsonResponse({'status': 'error', 'message': 'Start date, end date, and reason are required'}, status=400)

            s_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if e_date < s_date:
                return JsonResponse({'status': 'error', 'message': 'End date cannot be before start date'}, status=400)

            wfh_req = WFHRequest.objects.create(
                user=user,
                target_email=target_email or (user.email if user else ''),
                target_name=target_name or (user.get_full_name() if user else ''),
                leave_type=leave_type,
                start_date=s_date,
                end_date=e_date,
                reason=reason,
                status='pending'
            )

            return JsonResponse({
                'status': 'success',
                'message': 'WFH request submitted successfully for Admin approval.',
                'request_id': wfh_req.id
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def wfh_approve_api(request):
    """
    API for Admin/HR to Approve or Reject WFH applications.
    Upon approval, automatically creates/updates Attendance records with status='WFH'.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body) if request.body else request.POST
        request_id = data.get('request_id')
        action = data.get('action', 'approve').lower() # 'approve' or 'reject'
        admin_remarks = data.get('admin_remarks', '')

        if not request_id:
            return JsonResponse({'status': 'error', 'message': 'request_id is required'}, status=400)

        wfh_req = WFHRequest.objects.get(id=request_id)
        admin_user = request.user if request.user.is_authenticated else User.objects.first()

        if action == 'approve':
            wfh_req.status = 'approved'
            wfh_req.approved_by = admin_user
            wfh_req.admin_remarks = admin_remarks
            wfh_req.save()

            # Auto-Mark Attendance for every date in range
            curr_date = wfh_req.start_date
            academic_year = 'Jun 2025/2026'
            records_updated = 0

            while curr_date <= wfh_req.end_date:
                Attendance.objects.update_or_create(
                    user=wfh_req.user,
                    date=curr_date,
                    defaults={
                        'status': 'WFH',
                        'academic_year': academic_year,
                        'remarks': f'WFH Approved: {wfh_req.reason[:50]}'
                    }
                )
                curr_date += timedelta(days=1)
                records_updated += 1

            return JsonResponse({
                'status': 'success',
                'message': f'WFH Request approved! {records_updated} attendance record(s) marked as WFH.',
                'records_updated': records_updated
            })

        elif action == 'reject':
            wfh_req.status = 'rejected'
            wfh_req.approved_by = admin_user
            wfh_req.admin_remarks = admin_remarks
            wfh_req.save()

            return JsonResponse({
                'status': 'success',
                'message': 'WFH Request rejected.'
            })

        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid action. Must be approve or reject.'}, status=400)

    except WFHRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'WFH Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


