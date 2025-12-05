from django.contrib import admin
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.urls import path
from . import admin_views
from .models import Post, Comment



# Inline comments (Filament Relation Manager equivalent)

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request, obj):
        # Allow comments only on published posts by authenticated active users
        if not (request.user.is_authenticated and request.user.is_active):
            return False
        if obj is None:
            return False
        return getattr(obj, "status", None) == "published"

# POST ADMIN 

class PostAdmin(admin.ModelAdmin):

    list_display = ('id', 'title', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'content')
    inlines = [CommentInline]
    actions = ['soft_delete_posts', 'publish_posts']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Authors can see all posts (view-only for others), admin sees all
        return qs
#-> permission for the  regular user who can edit post
    def get_readonly_fields(self, request, obj=None):
        # Non-author (regular user) always read-only
        if not request.user.is_superuser and not request.user.is_author:
            return [f.name for f in self.model._meta.fields]
        # Author viewing someone else's post: all fields readonly
        if not request.user.is_superuser and obj and obj.author != request.user:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_view_permission(self, request, obj=None):
        # -> Allow any active user to view (regular users read-only)
        return request.user.is_authenticated and request.user.is_active

#-> permission for the superuser who can edit post
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return request.user.is_author
        # Allow authenticated users to open the change view to add inline comments.
        # Post fields stay read-only via get_readonly_fields for non-authors.
        if request.user.is_authenticated and request.user.is_active:
            return True
        return request.user.is_author and obj.author == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return request.user.is_author
        return request.user.is_author and obj.author == request.user

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.is_author

    # Ensure app and models appear for authenticated users (read-only users included)
    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.is_active

    # Auto-fill created_by / updated_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:             # New Post
            obj.created_by = request.user.email
        obj.updated_by = request.user.email
        super().save_model(request, obj, form, change)

    # Ensure inline comments set user automatically to the requester
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            if isinstance(inst, Comment) and not inst.pk:
                inst.user = request.user
                inst.created_by = request.user.email
            inst.updated_by = request.user.email
            inst.save()
        formset.save_m2m()

    # Soft delete action
    def soft_delete_posts(self, request, queryset):
        allowed = queryset
        if not request.user.is_superuser:
            allowed = queryset.filter(author=request.user)
        for post in allowed:
            post.soft_delete()
        self.message_user(request, "Selected posts moved to Trash.")
    soft_delete_posts.short_description = "Move selected posts to Trash"

    # Publish action
    def publish_posts(self, request, queryset):
        allowed = queryset
        if not request.user.is_superuser:
            allowed = queryset.filter(author=request.user)
        allowed.update(status='published')
        self.message_user(request, "Selected posts published.")
    publish_posts.short_description = "Publish selected posts"



# COMMENT ADMIN


class CommentAdmin(admin.ModelAdmin):

    list_display = ('id', 'post', 'user_id', 'created_at', 'updated_at')
    search_fields = ('content',)

    def get_readonly_fields(self, request, obj=None):
        # Regular users: read-only always
        if not request.user.is_superuser and not request.user.is_author:
            return [f.name for f in self.model._meta.fields]
        # Authors: read-only when viewing comments not authored by them
        if not request.user.is_superuser and obj and obj.user != request.user:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_view_permission(self, request, obj=None):
        # Any authenticated active user can view comments
        return request.user.is_authenticated and request.user.is_active

    def has_add_permission(self, request):
        # Allow any authenticated active user to add a comment via admin
        # Object-level ownership is still enforced on change/delete
        return request.user.is_authenticated and request.user.is_active

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            # Listing/edit form access only if user is author/admin; otherwise handled by readonly fields
            return request.user.is_author or (request.user.is_authenticated and request.user.is_active)
        # Authors can edit only their own comments
        return request.user.is_author and obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return request.user.is_author
        # Authors can delete only their own comments; regular users cannot delete
        return request.user.is_author and obj.user == request.user

    # Ensure app and models appear for authenticated users (read-only users included)
    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.is_active

    # Auto-fill created_by / updated_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:        # New Comment
            obj.created_by = request.user.email
        obj.updated_by = request.user.email
        super().save_model(request, obj, form, change)



# CUSTOM ADMIN SITE (like Filament custom pages)

class MyAdminSite(admin.AdminSite):
    site_header = "Blog Admin Panel"
    site_title = "Blog Admin"
    index_title = "Dashboard"

    # Allow any active authenticated user to access admin index/login
    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_active

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('author-page/', admin_views.author_page),
            path('user-page/', admin_views.user_page),
        ]
        return custom_urls + urls


# Custom authentication form to remove 'staff' wording
class BlogAdminAuthForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("This account is inactive.", code="inactive")
        # Regular users are permitted but will have read-only admin.


# Custom Admin Site Instance
admin_site = MyAdminSite(name='myadmin')
admin_site.login_form = BlogAdminAuthForm

# Register models with CUSTOM admin
admin_site.register(Post, PostAdmin)
admin_site.register(Comment, CommentAdmin)
