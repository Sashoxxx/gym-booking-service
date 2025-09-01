from django.urls import path

from gym.services.booking_sessions import (
    BookWorkoutSessionView,
    booking_success_view,
    CancelBookingView
)

from gym.views import (
    GymListView,
    GymDetailView,
    GymCreateView,
    GymUpdateView,
    GymDeleteView,
    WorkoutSessionCreateView,
    WorkoutSessionUpdateView,
    WorkoutSessionListView,
    WorkoutSessionDetailView,
    WorkoutSessionDeleteView,
    ToggleGymStatusView
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
        "<int:pk>/toggle-status/",
        ToggleGymStatusView.as_view(),
        name="gym-toggle-status"
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
        "<int:gym_pk>/sessions/<int:pk>/",
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
    path(
        "sessions/<int:pk>/delete/",
        WorkoutSessionDeleteView.as_view(),
        name="workout-session-delete"
    ),
    path(
        "sessions/<int:session_id>/book/",
        BookWorkoutSessionView.as_view(),
        name="book-session"
    ),
    path(
        "booking/<int:booking_id>/success/",
        booking_success_view,
        name="booking-success"
    ),
    path(
        "cancel-booking/<int:booking_id>/",
        CancelBookingView.as_view(),
        name="cancel-booking"
    ),
]

app_name = "gyms"
