from django.urls import path

from gym.views import (
    GymListView,
    GymDetailView,
    GymCreateView,
    GymUpdateView,
    GymDeleteView,
    WorkoutSessionCreateView,
    WorkoutSessionUpdateView,
    WorkoutSessionListView,
    WorkoutSessionDetailView
)

urlpatterns = [
    path(
        "",
        GymListView.as_view(),
        name="gym-list"
    ),
    path(
        "<int:pk>/",
        GymDetailView.as_view(),
        name="gym-detail"
    ),
    path(
        "create/",
        GymCreateView.as_view(),
        name="gym-create"
    ),
    path(
        "<int:pk>/update/",
        GymUpdateView.as_view(),
        name="gym-update"
    ),
    path(
        "<int:pk>/delete/",
        GymDeleteView.as_view(),
        name="gym-delete"
    ),
    path(
        "<int:gym_pk>/sessions/",
        WorkoutSessionListView.as_view(),
        name="workout-session-list"
    ),
    path(
        "int:gym_pk>/sessions/<int:pk>/",
        WorkoutSessionDetailView.as_view(),
        name="workout-session-detail"
    ),
    path(
        "<int:gym_pk>/sessions/create/",
        WorkoutSessionCreateView.as_view(),
        name="workout-session-create"
    ),
    path(
        "sessions/<int:pk>",
        WorkoutSessionUpdateView.as_view(),
        name="workout-session-update"
    ),
]

app_name = "gyms"
