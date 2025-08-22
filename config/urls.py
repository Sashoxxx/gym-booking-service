from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from config import settings
from gym.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", index, name="index"),
    path("gym/", include("gym.urls", namespace="gym")),
    path("users/", include("users.urls", namespace="users")),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
