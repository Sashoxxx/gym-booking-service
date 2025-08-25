from django.contrib import admin

from gym.models import WorkoutSession, Gym, Booking


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("name", "address")
    search_fields = ("name", "address")
    ordering = ("name",)
    list_filter = ("name",)


    def has_add_permission(self, request):
        return request.user.is_authenticated and (
                request.user.role == "admin" or request.user.is_superuser
        )

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and (
                request.user.role == "admin" or request.user.is_superuser
        )

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and (
                request.user.role == "admin" or request.user.is_superuser
        )


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "trainer", "start_time", "end_time")
    inlines = [BookingInline]

    def has_add_permission(self, request):
        return request.user.is_authenticated and (
                request.user.is_superuser or request.user.role in ["trainer", "admin"]
        )

    def has_change_permission(self, request, obj=None):
        if obj is not None and (
                request.user.role == "trainer" or request.user.is_superuser
        ):
            return obj.trainer == request.user
        return request.user.role == "admin"

    def has_delete_permission(self, request, obj=None):
        if obj is not None and (
                request.user.role == "trainer" or request.user.is_superuser
        ):
            return obj.trainer == request.user
        return request.user.role == "admin"
