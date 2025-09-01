from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        OFFICER = "officer", "Officer"
        INVESTIGATOR = "investigator", "Investigator"
        VIEWER = "viewer", "Viewer"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
