from django.urls import path

from users.views import (
    UserListView,
    UserDetailView,
    UserCreateView,
    UserDeleteView,
    AddBalanceView,
    StaffUserCreateView, UserUpdateView,
)

urlpatterns = [
    path("", UserListView.as_view(), name="user-list"),
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("create/", UserCreateView.as_view(), name="user-create"),
    path("<int:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),
    path("<int:pk>/update/", UserUpdateView.as_view(), name="user-update"),
    path("add-balance/", AddBalanceView.as_view(), name="add-balance"),
    path("create-staff/", StaffUserCreateView.as_view(), name="create-staff")
]

app_name = "users"
