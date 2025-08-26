import debug_toolbar
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from config import settings
from gym.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", index, name="index"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("gyms/", include("gym.urls", namespace="gyms")),
    path("users/", include("users.urls", namespace="users")),
                  path('__debug__/', include(debug_toolbar.urls)),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
