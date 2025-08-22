from django.urls import path

from gym.views import index


urlpatterns = [
    path("", index, name="index"),
]

app_name = "gym"