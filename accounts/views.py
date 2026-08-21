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
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .forms import DeleteAccountForm, ProfileForm, SignUpForm, UserEditForm
from .models import Profile, Role, User, AuditLog


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
        getattr(user, 'role', None) in ('staff', 'super_admin', 'teacher', 'admin', 'sales', 'sales_manager', 'employee')
    )


def _is_hr_or_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = (getattr(user, 'role', '') or '').lower()
    return role in ('admin', 'super_admin', 'hr', 'hr_manager', 'hr_head') or 'admin' in role or 'hr' in role



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

@csrf_exempt
@require_http_methods(['POST'])
def forgot_password_api(request):
    data = _body(request)
    identifier = (data.get('identifier', '') or data.get('username', '') or data.get('email', '')).strip()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not identifier:
        return JsonResponse({'success': False, 'error': 'Username or email address is required.'}, status=400)
    if not new_password or not confirm_password:
        return JsonResponse({'success': False, 'error': 'New password and confirm password are required.'}, status=400)
    if new_password != confirm_password:
        return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)
    if len(new_password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long.'}, status=400)

    user = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).first()
    if not user:
        return JsonResponse({'success': False, 'error': 'No account found with this username or email address.'}, status=404)

    user.set_password(new_password)
    user.save()
    return JsonResponse({'success': True, 'message': 'Password has been successfully updated.'})


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
    is_employee = request.GET.get('is_employee')
    if is_employee == 'true':
        qs = qs.filter(
            Q(role__in=['employee', 'sales', 'sales_manager', 'admin', 'staff', 'super_admin', 'teacher']) |
            Q(employee_profile__isnull=False) |
            Q(is_staff=True) |
            Q(is_superuser=True)
        ).exclude(role__in=['student', 'parent', 'institution'])


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


@csrf_exempt
@login_required
def employee_onboarding_api(request):
    """API for onboarding a new employee and viewing employee profiles"""
    def clean_id(val):
        if not val: return None
        s = str(val).strip()
        if s.lower() in ['null', 'undefined', 'none', '', '0']: return None
        return s

    if request.method == 'GET':
        # Ensure all employee role users have EmployeeProfiles
        emp_users = User.objects.filter(
            Q(role__in=['employee', 'sales', 'sales_manager', 'staff', 'teacher', 'admin']) |
            Q(employee_profile__isnull=False)
        ).distinct()
        
        for u in emp_users:
            if not hasattr(u, 'employee_profile') or u.employee_profile is None:
                emp_id = f"EMP-{u.id:04d}"
                EmployeeProfile.objects.get_or_create(
                    user=u,
                    defaults={'employee_id': emp_id, 'onboarding_status': 'active'}
                )

        user_id_query = request.GET.get('user_id')
        emp_id_query = request.GET.get('emp_id') or request.GET.get('id')

        u_param = clean_id(user_id_query)
        e_param = clean_id(emp_id_query)

        if u_param or e_param:
            emp = None

            # 1. Try lookup by emp_id / id as EmployeeProfile PK or code
            if e_param:
                if e_param.isdigit():
                    emp = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').filter(id=int(e_param)).first()
                if not emp:
                    emp = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').filter(employee_id=e_param).first()
                if not emp and e_param.isdigit():
                    emp = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').filter(user_id=int(e_param)).first()

            # 2. Try lookup by user_id
            if not emp and u_param:
                if u_param.isdigit():
                    emp = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').filter(user_id=int(u_param)).first()
                if not emp and u_param.isdigit():
                    emp = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').filter(id=int(u_param)).first()
                if not emp:
                    emp = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').filter(employee_id=u_param).first()

            # 3. Fallback: Auto-create/get EmployeeProfile if User exists
            if not emp:
                target_u = None
                for param in [u_param, e_param]:
                    if param and param.isdigit():
                        target_u = User.objects.filter(id=int(param)).first()
                        if target_u: break
                if target_u:
                    emp, _ = EmployeeProfile.objects.get_or_create(
                        user=target_u,
                        defaults={'employee_id': f"EMP-{target_u.id:04d}", 'onboarding_status': 'active'}
                    )
                    emp = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').filter(pk=emp.pk).first()
            
            if emp:
                u = emp.user
                extra_meta = {}
                if emp.notes:
                    if isinstance(emp.notes, dict):
                        extra_meta = emp.notes
                    elif isinstance(emp.notes, str) and emp.notes.strip():
                        try:
                            extra_meta = json.loads(emp.notes)
                        except Exception:
                            try:
                                import ast
                                extra_meta = ast.literal_eval(emp.notes)
                            except Exception:
                                pass

                dob_str = ''
                if getattr(u, 'date_of_birth', None):
                    try:
                        dob_str = u.date_of_birth.strftime('%Y-%m-%d')
                    except Exception:
                        dob_str = str(u.date_of_birth)
                elif extra_meta.get('date_of_birth'):
                    dob_str = extra_meta.get('date_of_birth')

                join_date_str = ''
                if emp.joining_date:
                    try: join_date_str = emp.joining_date.strftime('%Y-%m-%d')
                    except Exception: join_date_str = str(emp.joining_date)
                elif u.joining_date:
                    try: join_date_str = u.joining_date.strftime('%Y-%m-%d')
                    except Exception: join_date_str = str(u.joining_date)

                bg_val = extra_meta.get('blood_group', '') or extra_meta.get('bloodGroup', '')
                h_val = extra_meta.get('medical_height', '') or extra_meta.get('medicalHeight', '')
                w_val = extra_meta.get('medical_weight', '') or extra_meta.get('medicalWeight', '')
                d_val = extra_meta.get('medical_date', '') or extra_meta.get('medicalDate', '')
                acc_val = emp.bank_account_number or extra_meta.get('bank_account_number', '') or extra_meta.get('bankAccountNumber', '')
                bname_val = emp.bank_name or extra_meta.get('bank_name', '') or extra_meta.get('bankName', '')
                ifsc_val = emp.bank_ifsc or extra_meta.get('ifsc_code', '') or extra_meta.get('iFSCCode', '')
                nat_val = extra_meta.get('national_id', '') or extra_meta.get('nationalIdentificationNumber', '')
                epf_val = extra_meta.get('epf_no', '') or extra_meta.get('epfNo', '')
                sal_val = extra_meta.get('basic_salary', '') or extra_meta.get('basicSalary', '')
                curr_addr = extra_meta.get('current_address', '') or extra_meta.get('currentAddress', '')
                perm_addr = extra_meta.get('permanent_address', '') or extra_meta.get('permanentAddress', '')

                pwd_val = extra_meta.get('initial_password', '') or extra_meta.get('password', '') or 'Employee@123'

                return JsonResponse({
                    'status': 'success',
                    'employee': {
                        'id': emp.id,
                        'user_id': u.id,
                        'employee_id': emp.employee_id,
                        'full_name': u.get_full_name() or u.username,
                        'first_name': u.first_name or '',
                        'last_name': u.last_name or '',
                        'email': u.email or '',
                        'phone': u.phone or '',
                        'password': pwd_val,
                        'role': u.role or 'employee',
                        'department': emp.department.name if emp.department else '',
                        'department_id': emp.department_id,
                        'designation': emp.designation.title if emp.designation else '',
                        'designation_id': emp.designation_id,
                        'reporting_manager_id': emp.reporting_manager_id if emp.reporting_manager else '',
                        'joining_date': join_date_str,
                        'date_of_birth': dob_str,
                        'gender': u.gender or 'prefer_not_to_say',
                        'father_name': u.father_name or extra_meta.get('father_name', ''),
                        'mother_name': u.mother_name or extra_meta.get('mother_name', ''),
                        'marital_status': u.marital_status or 'single',
                        'contract_type': u.contract_type or 'full_time',
                        'shift': u.shift or 'morning',
                        'work_location': u.school_name or extra_meta.get('work_location', ''),
                        'facebook': u.facebook or '',
                        'linkedin': u.linkedin or '',
                        'instagram': u.instagram or '',
                        'blood_group': bg_val,
                        'bloodGroup': bg_val,
                        'medical_height': h_val,
                        'medicalHeight': h_val,
                        'medical_weight': w_val,
                        'medicalWeight': w_val,
                        'medical_date': d_val,
                        'medicalDate': d_val,
                        'bank_account_number': acc_val,
                        'bankAccountNumber': acc_val,
                        'bank_name': bname_val,
                        'bankName': bname_val,
                        'ifsc_code': ifsc_val,
                        'iFSCCode': ifsc_val,
                        'national_id': nat_val,
                        'nationalIdentificationNumber': nat_val,
                        'epf_no': epf_val,
                        'epfNo': epf_val,
                        'basic_salary': sal_val,
                        'basicSalary': sal_val,
                        'current_address': curr_addr,
                        'currentAddress': curr_addr,
                        'permanent_address': perm_addr,
                        'permanentAddress': perm_addr,
                        'profile_image': u.profile_image.url if u.profile_image else None
                    }
                })
            return JsonResponse({'status': 'error', 'message': 'Employee not found.'}, status=404)

        employees = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'reporting_manager').prefetch_related('documents').order_by('-created_at')
        data = []
        for emp in employees:
            dept_name = emp.department.name if emp.department else (emp.user.school_name or 'CRM & Sales')
            desig_title = emp.designation.title if emp.designation else (emp.user.role.title() if emp.user.role else 'Employee')
            join_str = emp.joining_date.strftime('%d %b %Y') if emp.joining_date else (emp.user.joining_date.strftime('%d %b %Y') if emp.user.joining_date else '19 Aug 2026')
            mgr_name = (emp.reporting_manager.get_full_name() or emp.reporting_manager.username) if emp.reporting_manager else 'Direct Super Admin'
            
            notes_dict = {}
            if emp.notes:
                if isinstance(emp.notes, dict):
                    notes_dict = emp.notes
                elif isinstance(emp.notes, str) and emp.notes.strip():
                    try:
                        notes_dict = json.loads(emp.notes)
                    except Exception:
                        pass
            raw_pwd = notes_dict.get('initial_password') or notes_dict.get('password') or 'Employee@123'

            data.append({
                'id': emp.id,
                'user_id': emp.user.id,
                'employee_id': emp.employee_id,
                'full_name': emp.user.get_full_name() or emp.user.username,
                'email': emp.user.email or 'N/A',
                'phone': emp.user.phone or 'N/A',
                'password': raw_pwd,
                'role': emp.user.role or 'employee',
                'department': dept_name,
                'designation': desig_title,
                'reporting_manager_id': emp.reporting_manager_id if emp.reporting_manager else None,
                'reporting_manager_name': mgr_name,
                'joining_date': join_str,
                'onboarding_status': emp.onboarding_status,
                'onboarding_status_display': emp.get_onboarding_status_display() if hasattr(emp, 'get_onboarding_status_display') else 'Active',
                'status': 'Active' if emp.user.is_active else 'Inactive',
                'docs_count': emp.documents.count(),
                'profile_image': emp.user.profile_image.url if emp.user.profile_image else None,
            })
        return JsonResponse({'status': 'success', 'data': data})

    elif request.method == 'POST':
        try:
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = request.POST
            else:
                try:
                    data = json.loads(request.body) if request.body else request.POST
                except Exception:
                    data = request.POST
            
            target_emp_id = data.get('emp_id') or data.get('id')
            full_name = data.get('fullName') or data.get('full_name') or ''
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            
            if full_name and not first_name:
                parts = full_name.strip().split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
            
            email = (data.get('myEmail') or data.get('employeeEmails') or data.get('email') or '').strip()
            phone = (data.get('phoneNumber') or data.get('phone') or '').strip()
            password = (data.get('your-password') or data.get('password') or '').strip()
            employee_id_input = (data.get('employeeID') or data.get('employee_id') or '').strip()

            department_val = data.get('employeeDepartment') or data.get('department')
            designation_val = data.get('employeeDesignation') or data.get('designation')
            access_role_input = data.get('employeeRole') or data.get('role') or data.get('access_level')
            reporting_manager_input = data.get('reportingManager') or data.get('reporting_manager') or data.get('reports_to')
            joining_date = data.get('joinDate') or data.get('joining_date') or None
            if joining_date == '': joining_date = None

            date_of_birth = data.get('dateOfBirth') or data.get('date_of_birth') or None
            if date_of_birth == '': date_of_birth = None

            gender = data.get('gender') or 'prefer_not_to_say'
            father_name = data.get('fathersName') or data.get('father_name') or ''
            mother_name = data.get('mothersName') or data.get('mother_name') or ''
            marital_status = data.get('meritalStatus') or data.get('marital_status') or 'single'
            contract_type = data.get('contractType') or data.get('contract_type') or 'full_time'
            shift = data.get('employeeShift') or data.get('shift') or 'morning'
            work_location = data.get('workLocation') or data.get('work_location') or ''
            
            blood_group = data.get('bloodGroup') or data.get('blood_group') or ''
            medical_height = data.get('medicalHeight') or data.get('medical_height') or ''
            medical_weight = data.get('medicalWeight') or data.get('medical_weight') or ''
            medical_date = data.get('medicalDate') or data.get('medical_date') or ''
            bank_account_number = data.get('bankAccountNumber') or data.get('bank_account_number') or ''
            bank_name = data.get('bankName') or data.get('bank_name') or ''
            ifsc_code = data.get('iFSCCode') or data.get('ifsc_code') or ''
            national_id = data.get('nationalIdentificationNumber') or data.get('national_id') or ''
            epf_no = data.get('epfNo') or data.get('companyName') or data.get('epf_no') or ''
            basic_salary = data.get('basicSalary') or data.get('Address') or data.get('basic_salary') or ''
            current_address = data.get('currentAddress') or data.get('current_address') or ''
            permanent_address = data.get('permanentAddress') or data.get('permanent_address') or ''

            facebook = data.get('facebookLink') or data.get('facebook') or ''
            linkedin = data.get('linkedInLink') or data.get('linkedin') or ''
            instagram = data.get('instagramLink') or data.get('instagram') or ''

            def norm_choice(val, choices_tuple):
                if not val: return choices_tuple[0][0]
                v_clean = str(val).strip().lower().replace(' ', '_').replace('/', '_')
                for k, lbl in choices_tuple:
                    if v_clean == k.lower() or v_clean in k.lower() or k.lower() in v_clean:
                        return k
                    if str(lbl).strip().lower() == str(val).strip().lower():
                        return k
                return val

            if not email:
                return JsonResponse({'status': 'error', 'message': 'Email address is required.'}, status=400)
            if not first_name:
                return JsonResponse({'status': 'error', 'message': 'Employee full name is required.'}, status=400)

            # Check if this is an EDIT / UPDATE operation for an existing employee
            user_id_input = data.get('user_id') or request.GET.get('user_id')
            emp_id_input = target_emp_id or data.get('emp_id') or data.get('id') or request.GET.get('emp_id') or request.GET.get('id')

            u_p = clean_id(user_id_input)
            e_p = clean_id(emp_id_input)
            existing_emp = None

            if e_p:
                if e_p.isdigit():
                    existing_emp = EmployeeProfile.objects.filter(id=int(e_p)).first()
                if not existing_emp:
                    existing_emp = EmployeeProfile.objects.filter(employee_id=e_p).first()
                if not existing_emp and e_p.isdigit():
                    existing_emp = EmployeeProfile.objects.filter(user_id=int(e_p)).first()

            if not existing_emp and u_p:
                if u_p.isdigit():
                    existing_emp = EmployeeProfile.objects.filter(user_id=int(u_p)).first()
                if not existing_emp and u_p.isdigit():
                    existing_emp = EmployeeProfile.objects.filter(id=int(u_p)).first()
                if not existing_emp:
                    existing_emp = EmployeeProfile.objects.filter(employee_id=u_p).first()

            if existing_emp:
                user = existing_emp.user
                # Check email and phone conflicts excluding current user
                if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                    return JsonResponse({'status': 'error', 'message': f'An account with email {email} already exists.'}, status=400)
                if phone and User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
                    return JsonResponse({'status': 'error', 'message': f'An account with phone number {phone} already exists.'}, status=400)
                
                user.first_name = first_name or ''
                user.last_name = last_name or ''
                user.email = email or ''
                user.phone = phone if phone else (user.phone or '')
                if access_role_input:
                    role_str = str(access_role_input).strip().lower()
                    if any(k in role_str for k in ['teacher', 'faculty', 'educator', 'teaching']):
                        user.role = 'teacher'
                    else:
                        user.role = role_str
                
                user.gender = norm_choice(gender, User.GenderChoices.choices)
                user.father_name = father_name or ''
                user.mother_name = mother_name or ''
                user.marital_status = norm_choice(marital_status, User.MaritalStatusChoices.choices)
                user.contract_type = norm_choice(contract_type, User.ContractTypeChoices.choices)
                user.shift = norm_choice(shift, User.ShiftChoices.choices)
                if joining_date: user.joining_date = joining_date
                if date_of_birth:
                    try: user.date_of_birth = date_of_birth
                    except Exception: pass

                user.school_name = work_location
                user.facebook = facebook
                user.linkedin = linkedin
                user.instagram = instagram

                if password:
                    user.set_password(password)

                profile_pic_file = request.FILES.get('profile_picture') or request.FILES.get('profile_image') or request.FILES.get('myFile')
                if profile_pic_file:
                    user.profile_image = profile_pic_file

                user.save()

                if employee_id_input:
                    existing_emp.employee_id = employee_id_input
                if joining_date:
                    existing_emp.joining_date = joining_date
                existing_emp.bank_account_number = bank_account_number
                existing_emp.bank_name = bank_name
                existing_emp.bank_ifsc = ifsc_code

                meta_dict = {
                    'date_of_birth': str(date_of_birth) if date_of_birth else '',
                    'father_name': father_name,
                    'mother_name': mother_name,
                    'work_location': work_location,
                    'blood_group': blood_group,
                    'medical_height': medical_height,
                    'medical_weight': medical_weight,
                    'medical_date': medical_date,
                    'bank_account_number': bank_account_number,
                    'bankAccountNumber': bank_account_number,
                    'bank_name': bank_name,
                    'bankName': bank_name,
                    'ifsc_code': ifsc_code,
                    'iFSCCode': ifsc_code,
                    'national_id': national_id,
                    'nationalIdentificationNumber': national_id,
                    'epf_no': epf_no,
                    'epfNo': epf_no,
                    'basic_salary': basic_salary,
                    'basicSalary': basic_salary,
                    'current_address': current_address,
                    'currentAddress': current_address,
                    'permanent_address': permanent_address,
                    'permanentAddress': permanent_address,
                }
                if password:
                    meta_dict['initial_password'] = password
                existing_emp.notes = json.dumps(meta_dict)

                # Department & Designation
                if department_val and department_val != 'Select':
                    if str(department_val).isdigit():
                        existing_emp.department = Department.objects.filter(id=department_val).first()
                    else:
                        dept_obj, _ = Department.objects.get_or_create(name=department_val.strip(), defaults={'code': str(department_val)[:10].upper()})
                        existing_emp.department = dept_obj

                if designation_val and designation_val != 'Select':
                    if str(designation_val).isdigit():
                        existing_emp.designation = Designation.objects.filter(id=designation_val).first()
                    else:
                        desig_obj = Designation.objects.filter(title__iexact=designation_val.strip()).first()
                        if not desig_obj:
                            desig_obj = Designation.objects.create(title=designation_val.strip(), department=existing_emp.department or Department.objects.first())
                        existing_emp.designation = desig_obj

                if reporting_manager_input:
                    mgr = User.objects.filter(id=reporting_manager_input).first()
                    if mgr:
                        existing_emp.reporting_manager = mgr

                existing_emp.save()

                return JsonResponse({
                    'status': 'success',
                    'message': f'Employee profile for {user.get_full_name()} updated successfully!',
                    'employee_id': existing_emp.employee_id,
                    'username': user.username,
                    'email': user.email
                })

            # New Employee Creation
            if not password:
                return JsonResponse({'status': 'error', 'message': 'Password is required for new employee.'}, status=400)

            # Check if email is already registered
            if User.objects.filter(email__iexact=email).exists():
                return JsonResponse({'status': 'error', 'message': f'An account with email {email} already exists.'}, status=400)

            # Generate unique username from email
            base_username = email.split('@')[0].replace('.', '_').replace('-', '_')
            username = base_username
            counter = 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            if not phone:
                phone = f"+9199{User.objects.count():08d}"
            elif User.objects.filter(phone=phone).exists():
                return JsonResponse({'status': 'error', 'message': f'An account with phone number {phone} already exists.'}, status=400)

            # Determine role explicitly or fallback from department
            role = 'employee'
            if access_role_input and str(access_role_input).strip():
                role_str = str(access_role_input).strip().lower()
                if any(k in role_str for k in ['teacher', 'faculty', 'educator', 'teaching']):
                    role = 'teacher'
                else:
                    role = role_str
            else:
                dept_str = str(department_val).lower() if department_val else ''
                if 'sales' in dept_str or 'crm' in dept_str:
                    role = 'sales'
                elif any(k in dept_str for k in ['teacher', 'faculty', 'educator', 'teaching']):
                    role = 'teacher'

            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role,
                gender=gender if gender in dict(User.GenderChoices.choices) else 'prefer_not_to_say',
                father_name=father_name,
                mother_name=mother_name,
                marital_status=marital_status if marital_status in dict(User.MaritalStatusChoices.choices) else 'single',
                contract_type=contract_type if contract_type in dict(User.ContractTypeChoices.choices) else 'full_time',
                shift=shift if shift in dict(User.ShiftChoices.choices) else 'morning',
                joining_date=joining_date,
                school_name=work_location,
                facebook=facebook,
                linkedin=linkedin,
                instagram=instagram,
                is_staff=True,
                is_active=True
            )
            user.set_password(password)
            
            profile_pic_file = request.FILES.get('profile_picture') or request.FILES.get('profile_image') or request.FILES.get('myFile')
            if profile_pic_file:
                user.profile_image = profile_pic_file
                
            user.save()

            # Handle Department & Designation ForeignKey lookup
            dept_obj = None
            if department_val and department_val != 'Select' and department_val.strip():
                if str(department_val).isdigit():
                    dept_obj = Department.objects.filter(id=department_val).first()
                else:
                    dept_obj, _ = Department.objects.get_or_create(
                        name=department_val.strip(),
                        defaults={'code': str(department_val)[:10].upper().replace(' ', '_')}
                    )

            if not dept_obj:
                dept_obj, _ = Department.objects.get_or_create(
                    name='General',
                    defaults={'code': 'GENERAL'}
                )

            desig_obj = None
            if designation_val and designation_val != 'Select' and designation_val.strip():
                if str(designation_val).isdigit():
                    desig_obj = Designation.objects.filter(id=designation_val).first()
                else:
                    desig_obj = Designation.objects.filter(title__iexact=designation_val.strip()).first()
                    if not desig_obj:
                        desig_obj = Designation.objects.create(
                            title=designation_val.strip(),
                            department=dept_obj
                        )

            # Lookup Reporting Manager User if provided
            reporting_mgr_user = None
            if reporting_manager_input and str(reporting_manager_input).strip():
                if str(reporting_manager_input).isdigit():
                    reporting_mgr_user = User.objects.filter(id=reporting_manager_input).first()
                else:
                    reporting_mgr_user = User.objects.filter(
                        Q(username__iexact=reporting_manager_input.strip()) |
                        Q(email__iexact=reporting_manager_input.strip())
                    ).first()

            emp_id = employee_id_input if employee_id_input else f"EMP-{user.id:04d}"
            if EmployeeProfile.objects.filter(employee_id=emp_id).exists():
                emp_id = f"EMP-{user.id:04d}-{User.objects.count()}"

            meta_dict = {
                'date_of_birth': str(date_of_birth) if date_of_birth else '',
                'father_name': father_name,
                'mother_name': mother_name,
                'work_location': work_location,
                'blood_group': blood_group,
                'medical_height': medical_height,
                'medical_weight': medical_weight,
                'medical_date': medical_date,
                'bank_account_number': bank_account_number,
                'bank_name': bank_name,
                'ifsc_code': ifsc_code,
                'national_id': national_id,
                'epf_no': epf_no,
                'basic_salary': basic_salary,
                'current_address': current_address,
                'permanent_address': permanent_address,
            }
            if password:
                meta_dict['initial_password'] = password

            emp_profile, created = EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': emp_id,
                    'department': dept_obj,
                    'designation': desig_obj,
                    'reporting_manager': reporting_mgr_user,
                    'joining_date': joining_date,
                    'onboarding_status': 'active',
                    'bank_account_number': bank_account_number,
                    'bank_name': bank_name,
                    'bank_ifsc': ifsc_code,
                    'notes': json.dumps(meta_dict)
                }
            )
            emp_profile.department = dept_obj
            emp_profile.designation = desig_obj
            emp_profile.reporting_manager = reporting_mgr_user
            emp_profile.bank_account_number = bank_account_number
            emp_profile.bank_name = bank_name
            emp_profile.bank_ifsc = ifsc_code
            emp_profile.notes = json.dumps(meta_dict)
            emp_profile.save()

            # Assign default checklist tasks
            default_tasks = ["ID Proof Submitted", "Work Email Created", "System Allocated", "HR Agreement Signed"]
            for task in default_tasks:
                OnboardingTask.objects.get_or_create(employee=emp_profile, title=task)

            return JsonResponse({
                'status': 'success',
                'message': 'Employee added successfully!',
                'employee_id': emp_id,
                'username': user.username,
                'email': user.email,
                'user_id': user.id
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


from .models import Attendance, AttendanceSetting
from datetime import date, datetime, timedelta

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

        matrix = {month_name: {} for month_name in month_map.values()}
        daily_records = []

        present_count = 0
        absent_count = 0
        half_day_count = 0
        late_count = 0
        holiday_count = 0
        wfh_count = 0

        for rec in records.order_by('-date'):
            m_name = month_map.get(rec.date.month)
            if m_name:
                matrix[m_name][rec.date.day] = rec.status
            
            st = rec.status
            if st == 'P': present_count += 1
            elif st == 'A': absent_count += 1
            elif st == 'F': half_day_count += 1
            elif st == 'L': late_count += 1
            elif st == 'H': holiday_count += 1
            elif st == 'WFH': wfh_count += 1

            c_in = rec.check_in.strftime('%I:%M %p') if rec.check_in else '-'
            c_out = rec.check_out.strftime('%I:%M %p') if rec.check_out else '-'

            work_duration = '-'
            if rec.check_in and rec.check_out:
                dt_in = datetime.combine(rec.date, rec.check_in)
                dt_out = datetime.combine(rec.date, rec.check_out)
                if dt_out > dt_in:
                    diff_sec = int((dt_out - dt_in).total_seconds())
                    hrs = diff_sec // 3600
                    mins = (diff_sec % 3600) // 60
                    if hrs > 0:
                        work_duration = f"{hrs}h {mins:02d}m" if mins > 0 else f"{hrs}h 00m"
                    else:
                        work_duration = f"{mins}m"

            st_display = rec.get_status_display()
            if rec.date.weekday() == 6 and st == 'H':
                st_display = 'Weekly Off'

            daily_records.append({
                'id': rec.id,
                'date': rec.date.strftime('%Y-%m-%d'),
                'formatted_date': rec.date.strftime('%d %b %Y'),
                'day_name': rec.date.strftime('%A'),
                'status': st,
                'status_display': st_display,
                'check_in': c_in,
                'check_out': c_out,
                'work_duration': work_duration,
                'remarks': rec.remarks or ('Weekly Off' if rec.date.weekday() == 6 else 'On Time')
            })

        return JsonResponse({
            'status': 'success',
            'user_id': user.id,
            'user_name': user.get_full_name() or user.username,
            'academic_year': academic_year,
            'summary': {
                'present': present_count,
                'absent': absent_count,
                'half_day': half_day_count,
                'late': late_count,
                'holiday': holiday_count,
                'wfh': wfh_count
            },
            'daily_records': daily_records,
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
         - Regular Employees: ONLY see their own requests.
         - HR & Admin: see all requests (or filter by employee if query params are provided).
    POST: Submit a new WFH application.
    """
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'success', 'data': []})

        reqs = WFHRequest.objects.select_related('user', 'approved_by').order_by('-applied_at')

        if _is_hr_or_admin(request.user):
            # Admin & HR can see all requests, or filter by requested employee if params provided
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
        else:
            # Regular Employee: STRICTLY ONLY view their own WFH/Leave requests
            user_email = request.user.email if request.user.email else '---'
            reqs = reqs.filter(
                Q(user=request.user) |
                Q(target_email__iexact=user_email)
            )

        req_type = request.GET.get('type')
        if req_type == 'wfh':
            reqs = reqs.filter(leave_type__icontains='Work From Home')
        elif req_type == 'leave':
            reqs = reqs.exclude(leave_type__icontains='Work From Home')

        data = []
        for r in reqs:
            data.append({
                'id': r.id,
                'user_id': r.user_id,
                'employee_name': r.target_name or (r.user.get_full_name() or r.user.username if r.user else 'Employee'),
                'email': r.target_email or (r.user.email if r.user else ''),
                'role': r.user.role if r.user and hasattr(r.user, 'role') else 'Staff',
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
            if _is_hr_or_admin(request.user):
                if target_email:
                    user = User.objects.filter(email__iexact=target_email).first()
                if not user and target_name:
                    user = User.objects.filter(
                        Q(first_name__icontains=target_name) |
                        Q(last_name__icontains=target_name) |
                        Q(username__icontains=target_name)
                    ).first()

            if not user or not request.user.is_authenticated:
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

            t_email = (user.email if user and user.email else target_email) or (request.user.email if request.user.is_authenticated else '')
            t_name = (user.get_full_name() or user.username if user else target_name) or (request.user.get_full_name() or request.user.username if request.user.is_authenticated else 'Employee')

            wfh_req = WFHRequest.objects.create(
                user=user,
                target_email=t_email,
                target_name=t_name,
                leave_type=leave_type,
                start_date=s_date,
                end_date=e_date,
                reason=reason,
                status='pending'
            )


            return JsonResponse({
                'status': 'success',
                'message': 'WFH / Leave request submitted successfully.',
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

    if not _is_hr_or_admin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Only HR and Admin can approve or reject WFH requests.'}, status=403)


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


@csrf_exempt
@login_required
def update_profile_image_api(request):
    """API for uploading and updating current user's profile image permanently in database"""
    if request.method == 'POST':
        image_file = request.FILES.get('profile_image') or request.FILES.get('profile_picture') or request.FILES.get('myFile')
        if image_file:
            request.user.profile_image = image_file
            request.user.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Profile picture updated successfully!',
                'image_url': request.user.profile_image.url
            })
        return JsonResponse({'status': 'error', 'message': 'No profile picture file provided.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@csrf_exempt
@login_required
def delete_employee_api(request, emp_id=None):
    """API for deleting an employee profile and associated User account"""
    if request.method not in ['POST', 'DELETE']:
        return JsonResponse({'status': 'error', 'message': 'POST or DELETE method required'}, status=405)

    if not _is_hr_or_admin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Only HR and Admin can delete employees.'}, status=403)

    try:
        if not emp_id:
            data = _body(request)
            emp_id = data.get('id') or data.get('employee_id')

        if not emp_id:
            return JsonResponse({'status': 'error', 'message': 'Employee ID is required.'}, status=400)

        # Try fetching by EmployeeProfile PK or employee_id string or User PK
        emp = EmployeeProfile.objects.filter(
            Q(id=emp_id) if str(emp_id).isdigit() else Q(employee_id=emp_id)
        ).first()

        if not emp and str(emp_id).isdigit():
            user = User.objects.filter(id=emp_id).first()
            if user and hasattr(user, 'employee_profile'):
                emp = user.employee_profile

        if not emp:
            return JsonResponse({'status': 'error', 'message': 'Employee profile not found.'}, status=404)

        user = emp.user
        emp_name = user.get_full_name() or user.username if user else 'Employee'
        
        # Prevent self deletion of logged in admin
        if user and user == request.user:
            return JsonResponse({'status': 'error', 'message': 'You cannot delete your own active account.'}, status=400)

        emp.delete()
        if user:
            user.delete()

        return JsonResponse({
            'status': 'success',
            'message': f'Employee {emp_name} deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@login_required
@require_POST
def update_profile_info_api(request):
    """API to update logged-in user's profile details (first_name, last_name, email, phone)"""
    try:
        data = _body(request)
        user = request.user
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()

        if first_name:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email:
            # Check unique email excluding current user
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                return JsonResponse({'status': 'error', 'message': 'Email address is already in use by another account.'}, status=400)
            user.email = email
        if phone is not None:
            user.phone = phone

        user.save()

        # Sync EmployeeProfile phone if present
        if hasattr(user, 'employee_profile') and user.employee_profile:
            emp = user.employee_profile
            if phone:
                emp.phone = phone
            emp.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Profile details updated successfully!',
            'user': {
                'full_name': user.get_full_name() or user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def _get_client_ip(request):
    """Extract client IP address from request META headers"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    if not ip or ip in ('127.0.0.1', '::1'):
        ip = request.META.get('HTTP_X_REAL_IP', '127.0.0.1')
    return ip


import math

def _calculate_distance_meters(lat1, lon1, lat2, lon2):
    """
    Calculate distance in meters between two lat/lon coordinates using Haversine formula.
    """
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


@csrf_exempt
@login_required
def attendance_settings_api(request):
    """
    API for getting and updating Global Attendance Timing & Geofence Location Settings.
    """
    settings_obj = AttendanceSetting.get_settings()

    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'settings': {
                'office_check_in_time': settings_obj.office_check_in_time.strftime('%H:%M'),
                'grace_period_minutes': settings_obj.grace_period_minutes,
                'office_check_out_time': settings_obj.office_check_out_time.strftime('%H:%M'),
                'office_location_name': settings_obj.office_location_name,
                'office_latitude': settings_obj.office_latitude,
                'office_longitude': settings_obj.office_longitude,
                'geofence_radius_meters': settings_obj.geofence_radius_meters,
                'enforce_geofence': settings_obj.enforce_geofence
            }
        })

    elif request.method == 'POST':
        if not _is_hr_or_admin(request.user):
            return JsonResponse({'status': 'error', 'message': 'Permission denied. Only HR/Admin can update shift and location settings.'}, status=403)
        try:
            data = _body(request)
            in_time_str = data.get('office_check_in_time')
            out_time_str = data.get('office_check_out_time')
            grace = data.get('grace_period_minutes')
            loc_name = data.get('office_location_name')
            lat = data.get('office_latitude')
            lng = data.get('office_longitude')
            radius = data.get('geofence_radius_meters')
            enforce = data.get('enforce_geofence')

            if in_time_str:
                settings_obj.office_check_in_time = datetime.strptime(in_time_str, '%H:%M').time()
            if out_time_str:
                settings_obj.office_check_out_time = datetime.strptime(out_time_str, '%H:%M').time()
            if grace is not None:
                settings_obj.grace_period_minutes = int(grace)
            if loc_name:
                settings_obj.office_location_name = str(loc_name).strip()
            if lat is not None and str(lat).strip() != '':
                settings_obj.office_latitude = float(lat)
            if lng is not None and str(lng).strip() != '':
                settings_obj.office_longitude = float(lng)
            if radius is not None:
                settings_obj.geofence_radius_meters = int(radius)
            if enforce is not None:
                settings_obj.enforce_geofence = bool(enforce)

            settings_obj.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Attendance shift timings and office location settings updated successfully!',
                'settings': {
                    'office_check_in_time': settings_obj.office_check_in_time.strftime('%H:%M'),
                    'grace_period_minutes': settings_obj.grace_period_minutes,
                    'office_check_out_time': settings_obj.office_check_out_time.strftime('%H:%M'),
                    'office_location_name': settings_obj.office_location_name,
                    'office_latitude': settings_obj.office_latitude,
                    'office_longitude': settings_obj.office_longitude,
                    'geofence_radius_meters': settings_obj.geofence_radius_meters,
                    'enforce_geofence': settings_obj.enforce_geofence
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@login_required
@require_GET
def attendance_today_status_api(request):
    """
    Get today's punch in / out status for the logged-in user, along with IP, location, timing settings, and employee details.
    """
    try:
        user = request.user
        today = date.today()
        att = Attendance.objects.filter(user=user, date=today).first()
        settings_obj = AttendanceSetting.get_settings()

        emp = getattr(user, 'employee_profile', None)
        emp_details = {
            'employee_id': emp.employee_id if emp else 'N/A',
            'full_name': user.get_full_name() or user.username,
            'email': user.email or 'N/A',
            'department': emp.department.name if emp and emp.department else 'N/A',
            'designation': emp.designation.title if emp and emp.designation else (user.role.title() if hasattr(user, 'role') else 'Staff'),
            'role': getattr(user, 'role', 'employee')
        }

        settings_data = {
            'office_check_in_time': settings_obj.office_check_in_time.strftime('%I:%M %p'),
            'grace_period_minutes': settings_obj.grace_period_minutes,
            'office_check_out_time': settings_obj.office_check_out_time.strftime('%I:%M %p'),
            'office_location_name': settings_obj.office_location_name,
            'is_admin': _is_hr_or_admin(user)
        }

        if not att:
            return JsonResponse({
                'status': 'success',
                'has_checked_in': False,
                'has_checked_out': False,
                'check_in_time': None,
                'check_out_time': None,
                'check_in_ip': None,
                'check_in_location': None,
                'check_out_ip': None,
                'check_out_location': None,
                'employee': emp_details,
                'shift_settings': settings_data
            })

        return JsonResponse({
            'status': 'success',
            'has_checked_in': att.check_in is not None,
            'has_checked_out': att.check_out is not None,
            'check_in_time': att.check_in.strftime('%I:%M %p') if att.check_in else None,
            'check_out_time': att.check_out.strftime('%I:%M %p') if att.check_out else None,
            'check_in_ip': att.check_in_ip or None,
            'check_in_location': att.check_in_location or None,
            'check_out_ip': att.check_out_ip or None,
            'check_out_location': att.check_out_location or None,
            'attendance_status': att.status,
            'attendance_status_display': att.get_status_display(),
            'employee': emp_details,
            'shift_settings': settings_data
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@login_required
@require_POST
def attendance_check_in_api(request):
    """
    Record Punch-In for logged in employee with IP, Geolocation (lat/lng/address), Automatic Late calculation, and Employee details.
    """
    try:
        user = request.user
        today = date.today()
        now_dt = datetime.now()
        now_time = now_dt.time()

        data = _body(request)
        lat = data.get('latitude')
        lng = data.get('longitude')
        loc_address = (data.get('location') or data.get('location_address') or '').strip()
        
        client_ip = _get_client_ip(request)

        if not loc_address and lat and lng:
            loc_address = f"Lat: {lat}, Lng: {lng}"
        elif not loc_address:
            loc_address = "GPS Location Not Provided"

        # Calculate Late Status based on Admin Attendance Settings
        settings_obj = AttendanceSetting.get_settings()

        # Validate Geofence if enabled by Admin
        if settings_obj.enforce_geofence and settings_obj.office_latitude and settings_obj.office_longitude:
            if lat is not None and lng is not None and str(lat).strip() != '' and str(lng).strip() != '':
                dist = _calculate_distance_meters(float(lat), float(lng), settings_obj.office_latitude, settings_obj.office_longitude)
                if dist > settings_obj.geofence_radius_meters:
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Punch-In rejected: You are {int(dist)}m away from {settings_obj.office_location_name}. Maximum allowed radius is {settings_obj.geofence_radius_meters}m."
                    }, status=400)

        exp_in_dt = datetime.combine(today, settings_obj.office_check_in_time)
        late_threshold_dt = exp_in_dt + timedelta(minutes=settings_obj.grace_period_minutes)

        is_late = now_dt > late_threshold_dt
        computed_status = 'L' if is_late else 'P'
        status_remark = f"Late Check-In ({now_time.strftime('%I:%M %p')}) - Shift Start: {settings_obj.office_check_in_time.strftime('%I:%M %p')} (+{settings_obj.grace_period_minutes}m Grace)" if is_late else f"On-Time Check-In ({now_time.strftime('%I:%M %p')})"

        att, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'academic_year': 'Jun 2025/2026',
                'status': computed_status,
                'check_in': now_time,
                'check_in_ip': client_ip,
                'check_in_location': loc_address,
                'check_in_latitude': float(lat) if (lat is not None and str(lat).strip() != '') else None,
                'check_in_longitude': float(lng) if (lng is not None and str(lng).strip() != '') else None,
                'remarks': status_remark
            }
        )

        if not created:
            att.check_in = now_time
            att.check_in_ip = client_ip
            att.check_in_location = loc_address
            att.status = computed_status
            att.remarks = status_remark
            if lat is not None and str(lat).strip() != '':
                att.check_in_latitude = float(lat)
            if lng is not None and str(lng).strip() != '':
                att.check_in_longitude = float(lng)
            att.save()

        emp = getattr(user, 'employee_profile', None)
        emp_details = {
            'employee_id': emp.employee_id if emp else 'N/A',
            'full_name': user.get_full_name() or user.username,
            'email': user.email or 'N/A',
            'department': emp.department.name if emp and emp.department else 'N/A',
            'designation': emp.designation.title if emp and emp.designation else (user.role.title() if hasattr(user, 'role') else 'Staff')
        }

        msg = f"Punch In recorded at {now_time.strftime('%I:%M %p')}. Marked as LATE (Shift start: {settings_obj.office_check_in_time.strftime('%I:%M %p')})" if is_late else f"Punch In recorded successfully at {now_time.strftime('%I:%M %p')}!"

        return JsonResponse({
            'status': 'success',
            'message': msg,
            'check_in_time': now_time.strftime('%I:%M %p'),
            'is_late': is_late,
            'attendance_status': computed_status,
            'attendance_status_display': 'Late' if is_late else 'Present',
            'ip_address': client_ip,
            'location': loc_address,
            'employee': emp_details
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@login_required
@require_POST
def attendance_check_out_api(request):
    """
    Record Punch-Out for logged in employee with IP, Geolocation (lat/lng/address), and Employee details.
    """
    try:
        user = request.user
        today = date.today()
        now_time = datetime.now().time()

        data = _body(request)
        lat = data.get('latitude')
        lng = data.get('longitude')
        loc_address = (data.get('location') or data.get('location_address') or '').strip()
        
        client_ip = _get_client_ip(request)

        if not loc_address and lat and lng:
            loc_address = f"Lat: {lat}, Lng: {lng}"
        elif not loc_address:
            loc_address = "GPS Location Not Provided"

        att = Attendance.objects.filter(user=user, date=today).first()
        if not att:
            att = Attendance.objects.create(
                user=user,
                date=today,
                academic_year='Jun 2025/2026',
                status='P'
            )

        att.check_out = now_time
        att.check_out_ip = client_ip
        att.check_out_location = loc_address
        if lat is not None and str(lat).strip() != '':
            att.check_out_latitude = float(lat)
        if lng is not None and str(lng).strip() != '':
            att.check_out_longitude = float(lng)
        att.save()

        emp = getattr(user, 'employee_profile', None)
        emp_details = {
            'employee_id': emp.employee_id if emp else 'N/A',
            'full_name': user.get_full_name() or user.username,
            'email': user.email or 'N/A',
            'department': emp.department.name if emp and emp.department else 'N/A',
            'designation': emp.designation.title if emp and emp.designation else (user.role.title() if hasattr(user, 'role') else 'Staff')
        }

        return JsonResponse({
            'status': 'success',
            'message': f"Punch Out recorded successfully at {now_time.strftime('%I:%M %p')}!",
            'check_out_time': now_time.strftime('%I:%M %p'),
            'ip_address': client_ip,
            'location': loc_address,
            'employee': emp_details
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_GET
@login_required
def audit_log_list_api(request):
    """
    API endpoint for listing system audit logs with pagination and filtering.
    """
    if not (request.user.is_superuser or getattr(request.user, 'role', '') in ['admin', 'superadmin']):
        return JsonResponse({'status': 'error', 'message': 'Access denied.'}, status=403)

    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        module = request.GET.get('module', '').strip()
        action = request.GET.get('action', '').strip()
        search = request.GET.get('q', '').strip()

        qs = AuditLog.objects.select_related('user').all()

        if module:
            qs = qs.filter(module__iexact=module)
        if action:
            qs = qs.filter(action__iexact=action)
        if search:
            qs = qs.filter(
                Q(description__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(object_id__icontains=search)
            )

        total_count = qs.count()
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1

        offset = (page - 1) * page_size
        logs = qs[offset:offset + page_size]

        results = []
        for log in logs:
            user_name = log.user.get_full_name() or log.user.username if log.user else 'System'
            results.append({
                'id': log.id,
                'user': user_name,
                'user_id': log.user.id if log.user else None,
                'action': log.action,
                'module': log.module,
                'object_id': log.object_id,
                'description': log.description,
                'ip_address': log.ip_address or 'N/A',
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return JsonResponse({
            'status': 'success',
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'results': results
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)




