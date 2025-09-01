from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active", "date_joined")
    fieldsets = (*DjangoUserAdmin.fieldsets, ("Role Info", {"fields": ("role",)}))
    add_fieldsets = (*DjangoUserAdmin.add_fieldsets, (None, {"fields": ("role",)}))
