from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.utils import timezone

from mainWebsite.models import LoginHistory



def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    ip         = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    now        = timezone.now()

    LoginHistory.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        status='success',
    )

    profile = getattr(user, 'profile', None)
    if profile:
        profile.is_online     = True
        profile.last_login_at = now
        profile.save(update_fields=['is_online', 'last_login_at'])


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if not user:
        return

    ip         = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    now        = timezone.now()

    LoginHistory.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        status='logout',
    )

    profile = getattr(user, 'profile', None)
    if profile:
        profile.is_online      = False
        profile.last_logout_at = now
        profile.save(update_fields=['is_online', 'last_logout_at'])


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    ip         = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    LoginHistory.objects.create(
        user=None,
        ip_address=ip,
        user_agent=user_agent,
        status='failed',
    )