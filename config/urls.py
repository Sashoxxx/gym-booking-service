from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from gym.views import IndexView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", IndexView.as_view(), name="index"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("gyms/", include("gym.urls", namespace="gyms")),
    path("users/", include("users.urls", namespace="users")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
