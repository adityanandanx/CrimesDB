from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


class SeedUserMixin:
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "seed-role-users/",
                self.admin_site.admin_view(self.seed_role_users),
                name="seed-role-users",
            ),
        ]
        return custom + urls

    def seed_role_users(self, request):
        if not request.user.is_staff:
            return redirect("admin:index")
        created = []
        defaults = {
            User.Roles.ADMIN: {"is_staff": True, "is_superuser": True},
            User.Roles.OFFICER: {"is_staff": True},
            User.Roles.INVESTIGATOR: {"is_staff": True},
            User.Roles.VIEWER: {"is_staff": False},
        }
        for role, extra in defaults.items():
            username = f"seed_{role}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="password123",
                    role=role,
                    **extra,
                )
                created.append(user.username)
        if created:
            messages.success(
                request, f"Created users: {', '.join(created)} (password: password123)"
            )
        else:
            messages.info(request, "All role users already exist.")
        return redirect("..")

    def changelist_view(self, request, extra_context=None):
        extra = extra_context or {}
        extra["seed_role_users_url"] = reverse("admin:seed-role-users")
        return super().changelist_view(request, extra_context=extra)


@admin.register(User)
class UserAdmin(SeedUserMixin, DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active", "date_joined")
    fieldsets = (*DjangoUserAdmin.fieldsets, ("Role Info", {"fields": ("role",)}))
    add_fieldsets = (*DjangoUserAdmin.add_fieldsets, (None, {"fields": ("role",)}))
