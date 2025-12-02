from django.contrib import admin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'is_author', 'mobile', 'created_at')
    search_fields = ('name', 'email', 'mobile')
    list_filter = ('is_author', 'created_at')
