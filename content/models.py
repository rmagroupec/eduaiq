from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class TeamMember(models.Model):
    """
    Team Member model for EduAiQ mentors, leadership, and instructors.
    Displayed on Homepage, About Us, Team page, and Individual Team Detail pages.
    """
    name = models.CharField(max_length=200, help_text="Full name of the team member")
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text="Unique URL slug (auto-generated if empty)")
    designation = models.CharField(max_length=200, help_text="e.g. AI Lab Mentor, Olympiad Lead, CEO")
    photo = models.ImageField(upload_to='team/', blank=True, null=True, help_text="Profile picture")
    quote = models.TextField(blank=True, default='', help_text="Inspirational quote or motto")
    bio = models.TextField(blank=True, default='', help_text="Detailed biography or introduction")
    
    # Contact & Social Links
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=40, blank=True, default='')
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    whatsapp_url = models.CharField(max_length=150, blank=True, default='')
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    
    # Career Details
    qualifications = models.TextField(
        blank=True, 
        default='', 
        help_text="Education & Qualifications history (e.g. year / degree / institute)"
    )
    experiences = models.TextField(
        blank=True, 
        default='', 
        help_text="Detailed experience summary and career achievements"
    )
    skills_overview = models.TextField(
        blank=True, 
        default='', 
        help_text="Key skills and proficiency levels (e.g. Completed Projects: 80, Financial Skills: 95)"
    )
    
    # Ordering & Visibility
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    is_active = models.BooleanField(default=True, help_text="Controls visibility across the website")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        return f"{self.name} ({self.designation})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "member"
            slug = base_slug
            counter = 1
            while TeamMember.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def photo_url(self):
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        return '/static/assets/img/educator-img8.png'


class BlogCategory(models.Model):
    """
    Categories for grouping blog articles (e.g. AI Lab, Olympiads, Careers, Technology).
    """
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "category"
            slug = base_slug
            counter = 1
            while BlogCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def post_count(self):
        return self.posts.filter(status='published').count()


class BlogPost(models.Model):
    """
    Blog Post / Article model for EduAiQ insights, student guides, and curriculum updates.
    """
    STATUS_CHOICES = (
        ('published', 'Published'),
        ('draft', 'Draft'),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    category = models.ForeignKey(
        BlogCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='posts'
    )
    author_name = models.CharField(max_length=150, blank=True, default='EduAiQ Team')
    author_team_member = models.ForeignKey(
        TeamMember, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='blog_posts'
    )
    featured_image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    summary = models.TextField(
        blank=True, 
        default='', 
        help_text="Short excerpt for cards, social share, and search results"
    )
    content = models.TextField(help_text="Full blog post content (HTML supported)")
    tags = models.CharField(
        max_length=255, 
        blank=True, 
        default='', 
        help_text="Comma-separated tags e.g. AI Skills, Olympiads, Careers"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    is_featured = models.BooleanField(default=False, help_text="Show in featured blog sections")
    views_count = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "post"
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.featured_image and hasattr(self.featured_image, 'url'):
            return self.featured_image.url
        return '/static/assets/img/educator-img12.jpg'

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def author_display(self):
        if self.author_team_member:
            return self.author_team_member.name
        return self.author_name or "EduAiQ Team"

