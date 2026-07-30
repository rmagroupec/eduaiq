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
        'email': user.email,
        'phone': user.phone,
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