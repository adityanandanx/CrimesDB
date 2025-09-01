import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "criminal.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
role = os.getenv("DJANGO_SUPERUSER_ROLE", "admin")

if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            password=password,
            email=email,
            role=role,
        )
        print(f"Created superuser '{username}'.")
    else:
        print(f"Superuser '{username}' already exists.")
else:
    print("Superuser env vars not fully set; skipping create_superuser.")
