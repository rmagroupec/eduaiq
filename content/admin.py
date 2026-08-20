from django.contrib import admin
from .models import TeamMember, BlogCategory, BlogPost


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'designation', 'bio')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author_display', 'status', 'is_featured', 'published_at', 'views_count')
    list_filter = ('status', 'is_featured', 'category', 'published_at')
    search_fields = ('title', 'summary', 'content', 'tags', 'author_name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'is_featured')

