"""
Courses Views — Pure JSON API
No template rendering. Every view returns JsonResponse.

Security notes:
- QuizQuestion.correct_option / explanation are NEVER sent to non-staff users
  except inside a graded attempt result, and only if quiz.show_correct_answers.
- Question options are shuffled per-request for students when the quiz has
  randomize_options enabled, exactly like get_shuffled_options() intends.
"""

import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db import models as dj_models
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CourseCategoryForm, CourseForm, CourseModuleForm, LessonForm, QuizForm
from .models import (
    Course, CourseCategory, CourseModule, Enrollment, Lesson,
    Quiz, QuizAccessLog, QuizAttempt, QuizQuestion,
)
from .utils import (
    get_allowed_courses_for_user,
    get_allowed_categories_for_user,
    is_course_accessible_by_user,
)


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
    return user.is_authenticated


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def _form_errors(form):
    return {field: errs for field, errs in form.errors.items()}


# ----------------------------------------------------------------------------
# Serializers
# ----------------------------------------------------------------------------

def serialize_category(c):
    return {
        'id': c.id, 'name': c.name, 'slug': c.slug, 'description': c.description,
        'icon': c.icon.url if c.icon else None, 'image': c.image.url if c.image else None,
        'color_code': c.color_code, 'is_active': c.is_active, 'order': c.order,
    }


def serialize_course(c, detailed=False, request=None):
    total_students = Enrollment.objects.filter(course=c).count()
    total_modules = c.modules.count()
    lessons_qs = Lesson.objects.filter(module__course=c)
    total_lessons = lessons_qs.count()

    thumbnail_url = None
    if c.thumbnail:
        thumbnail_url = request.build_absolute_uri(c.thumbnail.url) if request else c.thumbnail.url

    pdf_file_url = None
    if c.pdf_file:
        pdf_file_url = request.build_absolute_uri(c.pdf_file.url) if request else c.pdf_file.url

    data = {
        'id': c.id,
        'title': c.title,
        'slug': c.slug,
        'category': {
            'id': c.category.id,
            'name': c.category.name,
            'slug': c.category.slug,
            'color_code': c.category.color_code,
        },
        'category_name': c.category.name,
        'delivery_mode': c.delivery_mode,
        'description': c.description,
        'author': c.author or 'EduAiQ Editorial Team',
        'pdf_file': pdf_file_url,
        'level': 'beginner',
        'instructor': {
            'id': c.created_by.id,
            'username': c.created_by.username,
            'email': c.created_by.email or 'info@eduaiq.co.in',
            'phone': '+91 8052350041',
        } if c.created_by else None,
        'price': str(c.price),
        'status': c.status,
        'duration_weeks': 4,
        'thumbnail': thumbnail_url,
        'total_modules': total_modules,
        'total_lessons': total_lessons,
        'total_students': total_students,
        'average_rating': 4.8,
        'is_published': c.status == 'published',
        'is_live': c.is_live,                # NEW — published AND publish date has passed
        'is_coming_soon': c.is_coming_soon,   # NEW — approved, or published with a future date
        'created_by': c.created_by_id,
        'version': c.version,
        'published_at': c.published_at,
        'created_at': c.created_at,
        'updated_at': c.updated_at,
    }

    user = request.user if (request and hasattr(request, 'user')) else None
    data['is_accessible'] = is_accessible_by_user(user, c) if 'is_accessible_by_user' in globals() else is_course_accessible_by_user(user, c)

    if detailed:
        modules_list = []
        for m in c.modules.all().order_by('order'):
            module_lessons = m.lessons.all().order_by('order')
            lessons_data = []
            for l in module_lessons:
                lesson_file_url = None
                if l.content_file:
                    lesson_file_url = request.build_absolute_uri(l.content_file.url) if request else l.content_file.url
                lessons_data.append({
                    'id': l.id,
                    'title': l.title,
                    'description': l.description,
                    'content_type': l.content_type,
                    'content_url': l.content_url,
                    'content_file': lesson_file_url,
                    'duration_minutes': l.duration_minutes,
                    'order': l.order,
                    'is_preview': l.is_preview,
                    'is_published': l.is_published,
                })
            modules_list.append({
                'id': m.id,
                'title': m.title,
                'description': m.description,
                'order': m.order,
                'total_lessons': len(lessons_data),
                'lessons': lessons_data,
            })
        data['modules'] = modules_list

        quizzes_list = []
        quizzes_qs = Quiz.objects.filter(lesson__module__course=c, is_active=True)
        for q in quizzes_qs:
            quizzes_list.append({
                'id': q.id,
                'title': q.lesson.title,
                'description': q.lesson.description,
                'total_questions': q.questions.filter(is_active=True).count(),
                'passing_score_pct': q.passing_score_pct,
                'time_limit_minutes': q.time_limit_minutes,
            })
        data['quizzes'] = quizzes_list
        data['modules_count'] = total_modules
        data['reviewed_by'] = c.reviewed_by_id

    return data


def serialize_module(m):
    return {
        'id': m.id, 'course': m.course_id, 'title': m.title, 'description': m.description,
        'order': m.order, 'is_published': m.is_published, 'lessons_count': m.lessons.count(),
    }


def serialize_lesson(l):
    return {
        'id': l.id,
        'module': {
            'id': l.module.id,
            'title': l.module.title,
            'course_id': l.module.course_id,
        },
        'title': l.title,
        'description': l.description,
        'content_type': l.content_type,
        'content_url': l.content_url,
        'content_file': l.content_file.url if l.content_file else None,
        'duration_minutes': l.duration_minutes,
        'order': l.order,
        'is_preview': l.is_preview,
        'is_published': l.is_published,
        'has_quiz': l.content_type == 'quiz' and hasattr(l, 'quiz'),
        'created_at': l.created_at,
        'updated_at': l.updated_at,
    }


def serialize_quiz(q, include_settings=True):
    data = {
        'id': q.id, 'lesson': q.lesson_id,
        'time_limit_minutes': q.time_limit_minutes,
        'attempts_allowed': q.attempts_allowed,
        'passing_score_pct': q.passing_score_pct,
        'total_marks': q.total_marks,
        'question_count': q.questions.filter(is_active=True).count(),
    }
    if include_settings:
        data.update({
            'shuffle_questions': q.shuffle_questions,
            'show_correct_answers': q.show_correct_answers,
            'requires_authentication': q.requires_authentication,
            'enable_anti_cheating': q.enable_anti_cheating,
            'randomize_options': q.randomize_options,
            'shuffle_per_student': q.shuffle_per_student,
            'is_active': q.is_active,
        })
    return data


def serialize_question_admin(q):
    """Full view including the correct answer — staff only."""
    return {
        'id': q.id, 'quiz': q.quiz_id, 'order': q.order, 'marks': q.marks,
        'difficulty': q.difficulty, 'is_active': q.is_active,
        'question_text': q.question_text,
        'options': q.get_options(),
        'correct_option': q.correct_option,
        'explanation': q.explanation,
    }


def serialize_question_for_student(q):
    """Safe view for someone taking the quiz — never includes the answer."""
    options = q.get_shuffled_options() if q.quiz.randomize_options else q.get_options()
    return {
        'id': q.id, 'order': q.order, 'marks': q.marks,
        'question_text': q.question_text,
        'options': options,
    }


def serialize_attempt(a, reveal_answers=False):
    data = {
        'id': a.id, 'quiz': a.quiz_id, 'student': a.student_id,
        'attempt_number': a.attempt_number, 'status': a.status,
        'score_pct': str(a.score_pct) if a.score_pct is not None else None,
        'score_marks': a.score_marks, 'passed': a.passed,
        'started_at': a.started_at, 'submitted_at': a.submitted_at,
        'completed_at': a.completed_at, 'time_taken_minutes': a.time_taken_minutes,
        'cheating_detected': a.cheating_detected,
    }
    if reveal_answers:
        data['responses'] = a.student_responses
    return data


def serialize_enrollment(e, request=None):
    c = e.course
    thumbnail_url = None
    if c.thumbnail:
        thumbnail_url = request.build_absolute_uri(c.thumbnail.url) if request else c.thumbnail.url
    return {
        'id': e.id,
        'student': e.student_id,
        'course': {
            'id': c.id,
            'title': c.title,
            'slug': c.slug,
            'category': c.category.name,
            'instructor': c.created_by.username if c.created_by else 'N/A',
            'thumbnail': thumbnail_url,
        },
        'progress_pct': str(e.progress_pct),
        'is_completed': e.is_completed,
        'covered_by_plan': e.covered_by_plan,
        'amount_paid': str(e.amount_paid) if e.amount_paid is not None else None,
        'enrollment_date': e.enrollment_date,
        'completion_date': e.completion_date,
    }


def serialize_access_log(log):
    return {
        'id': log.id, 'quiz': log.quiz_id,
        'user': log.user_id, 'username': log.user.username if log.user else None,
        'action': log.action, 'ip_address': log.ip_address,
        'details': log.details, 'timestamp': log.timestamp,
    }


# ============================================================================
# COURSE CATEGORIES
# ============================================================================

@require_http_methods(['GET', 'POST'])
def category_list(request):
    if request.method == 'GET':
        qs = get_allowed_categories_for_user(request.user)
        return JsonResponse({
            'count': qs.count(),
            'results': [serialize_category(c) for c in qs]
        })

    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    form = CourseCategoryForm(_body(request))
    if form.is_valid():
        category = form.save()
        return JsonResponse({'success': True, 'category': serialize_category(category)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def category_detail(request, pk):
    try:
        category = CourseCategory.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)

    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'category': serialize_category(category)})
        if not request.user.is_superuser:
            allowed_cats = get_allowed_categories_for_user(request.user)
            if not allowed_cats.filter(pk=category.pk).exists():
                return JsonResponse({'error': 'This category is not allotted to your institution'}, status=403)
        return JsonResponse({'category': serialize_category(category)})

    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        try:
            category.delete()
            return JsonResponse({'success': True})
        except dj_models.ProtectedError:
            return JsonResponse({'error': 'Cannot delete category because it has active courses associated with it.'}, status=400)

    form = CourseCategoryForm(_body(request), instance=category)
    if form.is_valid():
        category = form.save()
        return JsonResponse({'success': True, 'category': serialize_category(category)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# COURSES
# ============================================================================

@require_http_methods(['GET', 'POST'])
def course_list(request):
    if request.method == 'GET':
        category = request.GET.get('category')
        exclude_param = request.GET.get('exclude_books')
        if exclude_param is not None:
            exclude_books = (exclude_param.lower() == 'true')
        else:
            exclude_books = (category != 'ai-books')

        qs = get_allowed_courses_for_user(request.user, exclude_books=exclude_books)

        if category:
            if str(category).isdigit():
                qs = qs.filter(category_id=int(category))
            else:
                qs = qs.filter(dj_models.Q(category__slug__iexact=category) | dj_models.Q(category__name__iexact=category))
        elif exclude_books:
            qs = qs.exclude(category__slug='ai-books')

        # ------------------------------------------------------------------
        # Public-safe view filter (NEW)
        # Non-staff callers can only ever see: published+live courses by
        # default, or coming-soon courses via ?view=coming_soon. They can
        # NOT pull arbitrary statuses (draft/in_review/archived etc.) — that
        # was previously an open gap since the old code only gated the
        # `status` param behind _is_staff() and otherwise applied no status
        # filter at all for anonymous/non-staff GETs.
        # ------------------------------------------------------------------
        view_mode = request.GET.get('view')  # 'live' (default) | 'coming_soon'
        if not _is_staff(request.user):
            now = timezone.now()
            if view_mode == 'coming_soon':
                qs = qs.filter(
                    dj_models.Q(status='approved') |
                    dj_models.Q(status='published', published_at__gt=now)
                )
            else:
                qs = qs.filter(status='published', published_at__lte=now)
        else:
            status = request.GET.get('status')
            if status:
                qs = qs.filter(status=status)
        # ------------------------------------------------------------------

        search = request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(title__icontains=search)
        
        try:
            page = max(int(request.GET.get('page', 1)), 1)
            page_size = min(max(int(request.GET.get('page_size', 12)), 1), 100)
        except ValueError:
            page, page_size = 1, 12

        count = qs.count()
        import math
        total_pages = math.ceil(count / page_size)
        start = (page - 1) * page_size
        results = qs[start:start + page_size]

        return JsonResponse({
            'count': count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'results': [serialize_course(c, request=request) for c in results]
        })

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    data = request.POST.copy() if request.POST else _body(request).copy()
    if not data.get('category'):
        cat_obj = CourseCategory.objects.filter(
            dj_models.Q(slug='ai-books') | dj_models.Q(name__icontains='AI Books')
        ).first()
        if not cat_obj:
            cat_obj = CourseCategory.objects.create(
                slug='ai-books',
                name='AI Books & Guides',
                description='AI E-Books & Guides Category'
            )
        elif cat_obj.slug != 'ai-books':
            cat_obj.slug = 'ai-books'
            cat_obj.save()
        data['category'] = str(cat_obj.id)

    form = CourseForm(data, request.FILES)
    if form.is_valid():
        course = form.save(commit=False)
        if not hasattr(course, 'category') or not course.category_id:
            course.category_id = int(data['category'])
        course.created_by = request.user
        try:
            course.save()
            from institutions.models import Institution
            inst = Institution.objects.filter(admin_user=request.user).first()
            if inst:
                course.institutions.add(inst)
                inst.allowed_courses.add(course)
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'course': serialize_course(course, detailed=True, request=request)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_course_or_404(slug):
    try:
        return Course.objects.select_related('category').get(slug=slug)
    except ObjectDoesNotExist:
        return None


def _can_manage_course(user, course):
    return user.is_authenticated


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def course_detail(request, slug):
    course = _get_course_or_404(slug)
    if course is None:
        return JsonResponse({'error': 'Course not found'}, status=404)

    if request.method == 'GET':
        if course.status != 'published' and not _can_manage_course(request.user, course):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        return JsonResponse({'course': serialize_course(course, detailed=True, request=request)})

    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        course.delete()
        return JsonResponse({'success': True})

    if request.method in ['PUT', 'PATCH'] and request.content_type.startswith('multipart/form-data'):
        from django.http.multipartparser import MultiPartParser
        parser = MultiPartParser(request.META, request, request.upload_handlers)
        put_data, put_files = parser.parse()
        form = CourseForm(put_data, put_files, instance=course)
    else:
        form = CourseForm(_body(request), request.FILES, instance=course)
    if form.is_valid():
        course = form.save(commit=False)
        try:
            course.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'course': serialize_course(course, detailed=True, request=request)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# COURSE MODULES
# ============================================================================

@require_http_methods(['GET', 'POST'])
def module_list(request, slug):
    course = _get_course_or_404(slug)
    if course is None:
        return JsonResponse({'error': 'Course not found'}, status=404)

    if request.method == 'GET':
        qs = course.modules.all().order_by('order')
        if not _can_manage_course(request.user, course):
            qs = qs.filter(is_published=True)
        return JsonResponse({'results': [serialize_module(m) for m in qs]})

    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    form = CourseModuleForm(_body(request))
    if form.is_valid():
        module = form.save(commit=False)
        module.course = course
        module.save()
        return JsonResponse({'success': True, 'module': serialize_module(module)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_module_or_404(pk):
    try:
        return CourseModule.objects.select_related('course').get(pk=pk)
    except ObjectDoesNotExist:
        return None


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def module_detail(request, pk):
    module = _get_module_or_404(pk)
    if module is None:
        return JsonResponse({'error': 'Module not found'}, status=404)

    if request.method == 'GET':
        if not module.is_published and not _can_manage_course(request.user, module.course):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'module': serialize_module(module)})

    if not _can_manage_course(request.user, module.course):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        module.delete()
        return JsonResponse({'success': True})

    form = CourseModuleForm(_body(request), instance=module)
    if form.is_valid():
        module = form.save()
        return JsonResponse({'success': True, 'module': serialize_module(module)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# LESSONS
# ============================================================================

@require_http_methods(['GET', 'POST'])
def lesson_list(request, pk):
    module = _get_module_or_404(pk)
    if module is None:
        return JsonResponse({'error': 'Module not found'}, status=404)

    if request.method == 'GET':
        qs = module.lessons.all().order_by('order')
        if not _can_manage_course(request.user, module.course):
            qs = qs.filter(is_published=True)
        return JsonResponse({'results': [serialize_lesson(l) for l in qs]})

    if not _can_manage_course(request.user, module.course):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    form = LessonForm(_body(request), request.FILES)
    if form.is_valid():
        lesson = form.save(commit=False)
        lesson.module = module
        try:
            lesson.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'lesson': serialize_lesson(lesson)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_lesson_or_404(pk):
    try:
        return Lesson.objects.select_related('module__course').get(pk=pk)
    except ObjectDoesNotExist:
        return None


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def lesson_detail(request, pk):
    lesson = _get_lesson_or_404(pk)
    if lesson is None:
        return JsonResponse({'error': 'Lesson not found'}, status=404)

    course = lesson.module.course

    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required to access lesson content.'}, status=401)
        if not is_course_accessible_by_user(request.user, course):
            return JsonResponse({'error': 'This course content is not allotted to your institution.'}, status=403)
        if not lesson.is_published and not _can_manage_course(request.user, course):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'lesson': serialize_lesson(lesson)})

    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        lesson.delete()
        return JsonResponse({'success': True})

    if request.method in ['PUT', 'PATCH'] and request.content_type.startswith('multipart/form-data'):
        from django.http.multipartparser import MultiPartParser
        parser = MultiPartParser(request.META, request, request.upload_handlers)
        put_data, put_files = parser.parse()
        form = LessonForm(put_data, put_files, instance=lesson)
    else:
        form = LessonForm(_body(request), request.FILES, instance=lesson)
    if form.is_valid():
        lesson = form.save(commit=False)
        try:
            lesson.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'lesson': serialize_lesson(lesson)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# QUIZ (one per lesson)
# ============================================================================

@require_http_methods(['GET', 'POST'])
def lesson_quiz(request, pk):
    lesson = _get_lesson_or_404(pk)
    if lesson is None:
        return JsonResponse({'error': 'Lesson not found'}, status=404)
    course = lesson.module.course

    if request.method == 'GET':
        try:
            quiz = lesson.quiz
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'This lesson has no quiz'}, status=404)
        return JsonResponse({'quiz': serialize_quiz(quiz, include_settings=_can_manage_course(request.user, course))})

    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if lesson.content_type != 'quiz':
        return JsonResponse({'error': "Lesson content_type must be 'quiz'"}, status=400)
    if hasattr(lesson, 'quiz'):
        return JsonResponse({'error': 'This lesson already has a quiz'}, status=400)

    form = QuizForm(_body(request))
    if form.is_valid():
        quiz = form.save(commit=False)
        quiz.lesson = lesson
        quiz.save()
        return JsonResponse({'success': True, 'quiz': serialize_quiz(quiz)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_quiz_or_404(pk):
    try:
        return Quiz.objects.select_related('lesson__module__course').get(pk=pk)
    except ObjectDoesNotExist:
        return None


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def quiz_detail(request, pk):
    quiz = _get_quiz_or_404(pk)
    if quiz is None:
        return JsonResponse({'error': 'Quiz not found'}, status=404)
    course = quiz.lesson.module.course

    if request.method == 'GET':
        quiz_data = serialize_quiz(quiz, include_settings=_can_manage_course(request.user, course))
        quiz_data['title'] = quiz.lesson.title
        quiz_data['description'] = quiz.lesson.description
        quiz_data['instructions'] = "Answer all questions. No negative marking."
        
        is_manager = _can_manage_course(request.user, course)
        qs = quiz.questions.filter(is_active=True).order_by('order')
        if is_manager:
            quiz_data['questions'] = [serialize_question_admin(q) for q in qs]
        else:
            quiz_data['questions'] = [serialize_question_for_student(q) for q in qs]
            
        return JsonResponse({'success': True, 'quiz': quiz_data})

    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        quiz.delete()
        return JsonResponse({'success': True})

    form = QuizForm(_body(request), instance=quiz)
    if form.is_valid():
        quiz = form.save()
        return JsonResponse({'success': True, 'quiz': serialize_quiz(quiz)})
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


# ============================================================================
# QUIZ QUESTIONS (correct_option/explanation are staff-only, always)
# ============================================================================

@require_http_methods(['GET', 'POST'])
def question_list(request, pk):
    quiz = _get_quiz_or_404(pk)
    if quiz is None:
        return JsonResponse({'error': 'Quiz not found'}, status=404)
    course = quiz.lesson.module.course
    is_manager = _can_manage_course(request.user, course)

    if request.method == 'GET':
        qs = quiz.questions.filter(is_active=True).order_by('order')
        if is_manager:
            return JsonResponse({'results': [serialize_question_admin(q) for q in qs]})
        return JsonResponse({'results': [serialize_question_for_student(q) for q in qs]})

    if not is_manager:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    data = _body(request)
    required = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return JsonResponse({'success': False, 'errors': {f: ['This field is required.'] for f in missing}}, status=400)

    question = QuizQuestion(quiz=quiz)
    question.question_text = data['question_text']
    question.option_a = data['option_a']
    question.option_b = data['option_b']
    question.option_c = data['option_c']
    question.option_d = data['option_d']
    question.correct_option = data['correct_option']
    if data.get('explanation'):
        question.explanation = data['explanation']
    question.marks = int(data.get('marks', 1))
    question.difficulty = data.get('difficulty', 'medium')
    question.order = int(data.get('order', quiz.questions.count() + 1))
    question.save()
    return JsonResponse({'success': True, 'question': serialize_question_admin(question)}, status=201)


def _get_question_or_404(pk):
    try:
        return QuizQuestion.objects.select_related('quiz__lesson__module__course').get(pk=pk)
    except ObjectDoesNotExist:
        return None


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def question_detail(request, pk):
    question = _get_question_or_404(pk)
    if question is None:
        return JsonResponse({'error': 'Question not found'}, status=404)
    course = question.quiz.lesson.module.course
    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        return JsonResponse({'question': serialize_question_admin(question)})

    if request.method == 'DELETE':
        question.delete()
        return JsonResponse({'success': True})

    data = _body(request)
    for field in ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'explanation']:
        if field in data:
            setattr(question, field, data[field])
    for field in ['marks', 'difficulty', 'order', 'is_active']:
        if field in data:
            setattr(question, field, data[field])
    question.save()
    return JsonResponse({'success': True, 'question': serialize_question_admin(question)})


# ============================================================================
# QUIZ-TAKING FLOW
# ============================================================================

@csrf_exempt
@login_required
@require_http_methods(['POST'])
def start_attempt(request, pk):
    quiz = _get_quiz_or_404(pk)
    if quiz is None:
        return JsonResponse({'error': 'Quiz not found'}, status=404)

    if not quiz.is_user_allowed(request.user):
        return JsonResponse({'error': 'You are not allowed to attempt this quiz right now.'}, status=403)

    attempt_number = QuizAttempt.objects.filter(quiz=quiz, student=request.user).count() + 1
    attempt = QuizAttempt.objects.create(
        quiz=quiz, student=request.user, attempt_number=attempt_number,
        score_pct=0, session_ip_address=_client_ip(request),
    )
    QuizAccessLog.objects.create(
        quiz=quiz, user=request.user, action='started',
        ip_address=_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    questions = quiz.questions.filter(is_active=True).order_by('order')
    if quiz.shuffle_questions:
        questions = list(questions)
        import random
        random.shuffle(questions)

    return JsonResponse({
        'attempt': serialize_attempt(attempt),
        'time_limit_minutes': quiz.time_limit_minutes,
        'questions': [serialize_question_for_student(q) for q in questions],
    }, status=201)


def _get_own_attempt_or_error(request, pk):
    try:
        attempt = QuizAttempt.objects.select_related('quiz').get(pk=pk)
    except ObjectDoesNotExist:
        return None, JsonResponse({'error': 'Attempt not found'}, status=404)
    if attempt.student_id != request.user.id and not _is_staff(request.user):
        return None, JsonResponse({'error': 'Forbidden'}, status=403)
    return attempt, None


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def submit_answer(request, pk):
    attempt, error = _get_own_attempt_or_error(request, pk)
    if error:
        return error
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'This attempt is no longer in progress.'}, status=400)

    data = _body(request)
    question_id = data.get('question_id')
    selected_option = data.get('selected_option')
    if not question_id or not selected_option:
        return JsonResponse({'error': 'question_id and selected_option are required'}, status=400)

    attempt.add_response(question_id, selected_option)
    attempt.save()
    return JsonResponse({'success': True})


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def submit_attempt(request, pk):
    attempt, error = _get_own_attempt_or_error(request, pk)
    if error:
        return error
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'This attempt has already been submitted.'}, status=400)

    now = timezone.now()
    attempt.submitted_at = now
    attempt.completed_at = now
    attempt.time_taken_minutes = max(1, int((now - attempt.started_at).total_seconds() // 60))
    attempt.status = 'graded'
    attempt.calculate_score()  # also saves

    QuizAccessLog.objects.create(
        quiz=attempt.quiz, user=request.user, action='submitted',
        ip_address=_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

    reveal = attempt.quiz.show_correct_answers
    result = serialize_attempt(attempt, reveal_answers=True)
    if reveal:
        result['correct_answers'] = {
            str(q.id): q.correct_option
            for q in attempt.quiz.questions.filter(is_active=True)
        }
        feedback_dict = {}
        for q in attempt.quiz.questions.filter(is_active=True):
            student_ans = attempt.get_response(q.id)
            correct_ans = q.correct_option
            is_correct = student_ans == correct_ans
            expl = q.explanation or ""
            feedback_dict[str(q.id)] = f"{'Correct!' if is_correct else 'Incorrect!'} {expl}".strip()
        result['feedback'] = feedback_dict
    return JsonResponse({'success': True, 'result': result, 'attempt': result})


@login_required
@require_GET
def attempt_detail(request, pk):
    attempt, error = _get_own_attempt_or_error(request, pk)
    if error:
        return error
    reveal = attempt.status == 'graded'
    return JsonResponse({'attempt': serialize_attempt(attempt, reveal_answers=reveal)})


@login_required
@require_GET
def my_attempts(request):
    qs = QuizAttempt.objects.filter(student=request.user).order_by('-started_at')
    quiz_id = request.GET.get('quiz')
    if quiz_id:
        qs = qs.filter(quiz_id=quiz_id)
    return JsonResponse({'results': [serialize_attempt(a) for a in qs]})


# ============================================================================
# ENROLLMENTS
# ============================================================================

@login_required
@require_http_methods(['POST'])
def enroll_course(request, slug):
    course = _get_course_or_404(slug)
    if course is None:
        return JsonResponse({'error': 'Course not found'}, status=404)
    if course.status != 'published':
        return JsonResponse({'error': 'This course is not open for enrollment.'}, status=400)

    data = _body(request)
    student_id = data.get('student_id')

    if not student_id:
        return JsonResponse({'error': 'student_id is required. Only Institution Admins can allot courses to students.'}, status=400)

    try:
        student = User.objects.get(pk=student_id, role='student')
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Student not found.'}, status=404)

    # Get student's institution
    if not hasattr(student, 'student_profile') or not student.student_profile.institution:
        return JsonResponse({'error': 'Student does not belong to any institution.'}, status=400)
    
    institution = student.student_profile.institution

    # Check if request.user is the Admin of this institution or a Super Admin
    if institution.admin_user_id != request.user.id and not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden. Only the Institution Admin or Super Admin can allot courses to this student.'}, status=403)

    # Check if the course is allotted to the institution by the Main Admin
    if not institution.allowed_courses.filter(pk=course.pk).exists():
        return JsonResponse({'error': 'This course is not allotted to your institution by the Main Admin.'}, status=403)

    if Enrollment.objects.filter(student=student, course=course).exists():
        return JsonResponse({'error': 'Student is already enrolled in this course.'}, status=400)

    covered_by_plan = bool(data.get('covered_by_plan', False))
    amount_paid = data.get('amount_paid', 0 if covered_by_plan else course.price)

    enrollment = Enrollment(
        student=student, course=course,
        covered_by_plan=covered_by_plan, amount_paid=amount_paid,
    )
    try:
        enrollment.save()
    except DjangoValidationError as e:
        return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)

    return JsonResponse({
        'success': True,
        'enrollment': {
            'id': enrollment.id,
            'student': {
                'id': student.id,
                'username': student.username,
                'email': student.email or 'info@eduaiq.co.in',
            },
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
            },
            'progress_pct': str(enrollment.progress_pct),
            'is_completed': enrollment.is_completed,
            'covered_by_plan': enrollment.covered_by_plan,
            'amount_paid': str(enrollment.amount_paid) if enrollment.amount_paid is not None else "0.00",
            'enrollment_date': enrollment.enrollment_date,
            'completion_date': enrollment.completion_date,
        }
    }, status=201)


@login_required
@require_GET
def my_enrollments(request):
    qs = Enrollment.objects.filter(student=request.user).select_related('course').order_by('-enrollment_date')
    
    try:
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(max(int(request.GET.get('page_size', 12)), 1), 100)
    except ValueError:
        page, page_size = 1, 12

    count = qs.count()
    import math
    total_pages = math.ceil(count / page_size)
    start = (page - 1) * page_size
    results = qs[start:start + page_size]

    return JsonResponse({
        'count': count,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': [serialize_enrollment(e, request=request) for e in results]
    })


@login_required
@require_http_methods(['PATCH', 'PUT'])
def update_progress(request, pk):
    try:
        enrollment = Enrollment.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Enrollment not found'}, status=404)
    if enrollment.student_id != request.user.id and not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    data = _body(request)
    if 'progress_pct' in data:
        enrollment.progress_pct = data['progress_pct']
    enrollment.last_accessed_at = timezone.now()
    if enrollment.progress_pct >= 100 and not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()

    try:
        enrollment.save()
    except DjangoValidationError as e:
        return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)

    return JsonResponse({
        'success': True,
        'enrollment': {
            'id': enrollment.id,
            'progress_pct': str(enrollment.progress_pct),
            'is_completed': enrollment.is_completed,
            'completion_date': enrollment.completion_date,
        }
    })


# ============================================================================
# QUIZ ACCESS LOGS (staff only — audit trail)
# ============================================================================

@login_required
@require_GET
def quiz_access_logs(request, pk):
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    quiz = _get_quiz_or_404(pk)
    if quiz is None:
        return JsonResponse({'error': 'Quiz not found'}, status=404)
    logs = quiz.access_logs.select_related('user').order_by('-timestamp')[:200]
    return JsonResponse({'results': [serialize_access_log(l) for l in logs]})


# ============================================================================
# ADMIN QUIZ MANAGEMENT VIEWS
# ============================================================================

@login_required
@require_GET
def quiz_list(request):
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    qs = Quiz.objects.select_related('lesson__module__course').all()
    results = []
    for q in qs:
        results.append({
            'id': q.id,
            'title': q.lesson.title,
            'course_title': q.lesson.module.course.title,
            'course_slug': q.lesson.module.course.slug,
            'module_title': q.lesson.module.title,
            'total_questions': q.questions.count(),
            'time_limit_minutes': q.time_limit_minutes,
            'passing_score_pct': q.passing_score_pct,
            'attempts_allowed': q.attempts_allowed,
            'enable_anti_cheating': q.enable_anti_cheating,
            'is_active': q.is_active,
        })
    return JsonResponse({'results': results})


@login_required
@require_GET
def admin_attempts(request):
    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    qs = QuizAttempt.objects.select_related('student', 'quiz__lesson').order_by('-started_at')
    
    quiz_id = request.GET.get('quiz')
    if quiz_id:
        qs = qs.filter(quiz_id=quiz_id)
        
    student_id = request.GET.get('student')
    if student_id:
        qs = qs.filter(student_id=student_id)
        
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
        
    results = []
    for a in qs:
        results.append({
            'id': a.id,
            'quiz_id': a.quiz_id,
            'quiz_title': a.quiz.lesson.title,
            'student_id': a.student_id,
            'student_username': a.student.username,
            'student_name': f"{a.student.first_name} {a.student.last_name}".strip() or a.student.username,
            'score_pct': float(a.score_pct) if a.score_pct is not None else 0.0,
            'score_marks': a.score_marks,
            'passed': a.passed,
            'attempt_number': a.attempt_number,
            'status': a.status,
            'started_at': a.started_at.isoformat() if a.started_at else None,
            'submitted_at': a.submitted_at.isoformat() if a.submitted_at else None,
            'completed_at': a.completed_at.isoformat() if a.completed_at else None,
            'time_taken_minutes': a.time_taken_minutes,
            'cheating_detected': a.cheating_detected,
            'cheating_details': a.cheating_details,
        })
    return JsonResponse({'results': results})


@csrf_exempt
@require_http_methods(['POST'])
def enroll_course(request, slug):
    if not request.user or not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in first.'}, status=401)

    course = _get_course_or_404(slug)
    if not course:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={
            'amount_paid': course.price,
            'covered_by_plan': False
        }
    )

    inst = get_user_institution(request.user)
    if inst:
        inst.allowed_courses.add(course)

    return JsonResponse({
        'success': True,
        'message': f'Successfully enrolled in {course.title}!',
        'enrolled': True,
        'course_slug': course.slug
    })