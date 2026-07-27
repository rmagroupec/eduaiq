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
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CourseCategoryForm, CourseForm, CourseModuleForm, LessonForm, QuizForm
from .models import (
    Course, CourseCategory, CourseModule, Enrollment, Lesson,
    Quiz, QuizAccessLog, QuizAttempt, QuizQuestion,
)


# ============================================================================
# HELPERS
# ============================================================================

def _body(request):
    if request.body:
        try:
            return json.loads(request.body)
        except (ValueError, TypeError):
            pass
    return request.POST.dict()


def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


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


def serialize_course(c, detailed=False):
    data = {
        'id': c.id, 'title': c.title, 'slug': c.slug,
        'category': c.category_id, 'category_name': c.category.name,
        'delivery_mode': c.delivery_mode, 'description': c.description,
        'thumbnail': c.thumbnail.url if c.thumbnail else None,
        'price': str(c.price), 'status': c.status,
        'created_by': c.created_by_id, 'version': c.version,
        'published_at': c.published_at, 'created_at': c.created_at,
    }
    if detailed:
        data['modules_count'] = c.modules.count()
        data['reviewed_by'] = c.reviewed_by_id
    return data


def serialize_module(m):
    return {
        'id': m.id, 'course': m.course_id, 'title': m.title, 'description': m.description,
        'order': m.order, 'is_published': m.is_published, 'lessons_count': m.lessons.count(),
    }


def serialize_lesson(l):
    return {
        'id': l.id, 'module': l.module_id, 'title': l.title, 'description': l.description,
        'content_type': l.content_type, 'content_url': l.content_url,
        'content_file': l.content_file.url if l.content_file else None,
        'duration_minutes': l.duration_minutes, 'order': l.order,
        'is_preview': l.is_preview, 'is_published': l.is_published,
        'has_quiz': l.content_type == 'quiz' and hasattr(l, 'quiz'),
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


def serialize_enrollment(e):
    return {
        'id': e.id, 'student': e.student_id, 'course': e.course_id,
        'course_title': e.course.title, 'covered_by_plan': e.covered_by_plan,
        'amount_paid': str(e.amount_paid), 'progress_pct': str(e.progress_pct),
        'is_completed': e.is_completed, 'completed_at': e.completed_at,
        'last_accessed_at': e.last_accessed_at, 'enrolled_at': e.enrolled_at,
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
        qs = CourseCategory.objects.all().order_by('order', 'name')
        if not _is_staff(request.user):
            qs = qs.filter(is_active=True)
        return JsonResponse({'results': [serialize_category(c) for c in qs]})

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
        return JsonResponse({'category': serialize_category(category)})

    if not _is_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        category.delete()
        return JsonResponse({'success': True})

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
        qs = Course.objects.select_related('category').all()
        if not _is_staff(request.user):
            qs = qs.filter(status='published')
        category = request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        status = request.GET.get('status')
        if status and _is_staff(request.user):
            qs = qs.filter(status=status)
        search = request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(title__icontains=search)
        return JsonResponse({'results': [serialize_course(c) for c in qs]})

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    data = _body(request)
    form = CourseForm(data)
    if form.is_valid():
        course = form.save(commit=False)
        course.created_by = request.user
        try:
            course.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'course': serialize_course(course, detailed=True)}, status=201)
    return JsonResponse({'success': False, 'errors': _form_errors(form)}, status=400)


def _get_course_or_404(slug):
    try:
        return Course.objects.select_related('category').get(slug=slug)
    except ObjectDoesNotExist:
        return None


def _can_manage_course(user, course):
    return _is_staff(user) or (user.is_authenticated and course.created_by_id == user.id)


@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def course_detail(request, slug):
    course = _get_course_or_404(slug)
    if course is None:
        return JsonResponse({'error': 'Course not found'}, status=404)

    if request.method == 'GET':
        if course.status != 'published' and not _can_manage_course(request.user, course):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'course': serialize_course(course, detailed=True)})

    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        course.delete()
        return JsonResponse({'success': True})

    form = CourseForm(_body(request), instance=course)
    if form.is_valid():
        course = form.save(commit=False)
        try:
            course.save()
        except DjangoValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)
        return JsonResponse({'success': True, 'course': serialize_course(course, detailed=True)})
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
    form = LessonForm(_body(request))
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
        if not lesson.is_published and not _can_manage_course(request.user, course):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return JsonResponse({'lesson': serialize_lesson(lesson)})

    if not _can_manage_course(request.user, course):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'DELETE':
        lesson.delete()
        return JsonResponse({'success': True})

    form = LessonForm(_body(request), instance=lesson)
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


@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def quiz_detail(request, pk):
    quiz = _get_quiz_or_404(pk)
    if quiz is None:
        return JsonResponse({'error': 'Quiz not found'}, status=404)
    course = quiz.lesson.module.course
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
    return JsonResponse({'success': True, 'result': result})


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
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return JsonResponse({'error': 'You are already enrolled in this course.'}, status=400)

    data = _body(request)
    covered_by_plan = bool(data.get('covered_by_plan', False))
    amount_paid = data.get('amount_paid', 0 if covered_by_plan else course.price)

    enrollment = Enrollment(
        student=request.user, course=course,
        covered_by_plan=covered_by_plan, amount_paid=amount_paid,
    )
    try:
        enrollment.save()
    except DjangoValidationError as e:
        return JsonResponse({'success': False, 'errors': e.message_dict}, status=400)

    return JsonResponse({'success': True, 'enrollment': serialize_enrollment(enrollment)}, status=201)


@login_required
@require_GET
def my_enrollments(request):
    qs = Enrollment.objects.filter(student=request.user).select_related('course').order_by('-enrolled_at')
    return JsonResponse({'results': [serialize_enrollment(e) for e in qs]})


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

    return JsonResponse({'success': True, 'enrollment': serialize_enrollment(enrollment)})


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