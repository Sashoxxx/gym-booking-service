from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models import Account

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "phone_number",
        "is_staff",
        "is_superuser",
    )
    list_filter = ("role", "is_staff", "is_superuser")
    search_fields = ("username", "email")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("account_type", "balance", "created_at")
    list_filter = ("account_type",)
    search_fields = ("user__username", "gym__name")
