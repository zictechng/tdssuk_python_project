# dashboard/middleware.py

from django.shortcuts import redirect
from django.conf import settings


class DashboardAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Only apply to dashboard
        if path.startswith('/dashboard/') and not path.startswith('/dashboard/auth/'):
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL or '/dashboard/auth/login/')

        return self.get_response(request)