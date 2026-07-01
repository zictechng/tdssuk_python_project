

from mainWebsite.models import SystemSetting


def general_settings(request):
    setting = SystemSetting.objects.first()
    return {'setting': setting}