from django.shortcuts import redirect
from django.contrib.auth import logout


def logout_view(request):
    """Log the user out on GET or POST then redirect to login."""
    if request.method in ("GET", "POST"):
        logout(request)
    return redirect("login")
