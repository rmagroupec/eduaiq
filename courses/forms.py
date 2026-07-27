"""
Courses Forms
ModelForms for models with plain fields. QuizQuestion is handled manually in
views.py since its text fields are encrypted properties, not real model fields.
"""

from django import forms

from .models import Course, CourseCategory, CourseModule, Enrollment, Lesson, Quiz


class CourseCategoryForm(forms.ModelForm):
    class Meta:
        model = CourseCategory
        fields = ['name', 'slug', 'description', 'color_code', 'is_active', 'order']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'slug', 'category', 'delivery_mode', 'description', 'price', 'status']


class CourseModuleForm(forms.ModelForm):
    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'order', 'is_published']


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'content_type', 'content_url',
            'duration_minutes', 'order', 'is_preview', 'is_published',
        ]


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'passing_score_pct', 'time_limit_minutes', 'shuffle_questions',
            'show_correct_answers', 'attempts_allowed', 'requires_authentication',
            'enable_anti_cheating', 'randomize_options', 'shuffle_per_student', 'is_active',
        ]