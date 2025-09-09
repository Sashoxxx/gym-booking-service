from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import Prefetch, Q
from django.db.models.aggregates import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView,
    UpdateView,
    CreateView, TemplateView,
)

from gym.forms import WorkoutSessionForm
from gym.models import Gym, WorkoutSession, Booking


User = get_user_model()


class IndexView(TemplateView):
    template_name = "gyms/index.html"

    def get_context_data(self, **kwargs):
        request: HttpRequest = self.request
        context = super().get_context_data(**kwargs)

        if not request.session.session_key:
            request.session.create()

        num_visits = request.session.get("num_visits", 1)
        request.session["num_visits"] = num_visits + 1

        num_gyms = Gym.objects.count()
        total_trainers = WorkoutSession.objects.values("trainer").distinct().count()
        total_clients = Booking.objects.values("user").distinct().count()

        context.update({
            "num_gyms": num_gyms,
            "total_trainers": total_trainers,
            "total_clients": total_clients,
            "num_visits": num_visits,
        })

        return context


class GymListView(ListView):
    model = Gym
    template_name = "gyms/gym_list.html"
    context_object_name = "gyms"
    paginate_by = 6

    def get_queryset(self):
        return Gym.objects.prefetch_related("sessions").order_by("name")


class GymDetailView(DetailView):
    model = Gym
    template_name = "gyms/gym_detail.html"
    context_object_name = "gym"

    def get_queryset(self):
        return Gym.objects.prefetch_related("sessions")


class GymCreateView(PermissionRequiredMixin, CreateView):
    model = Gym
    fields = ["name", "address", "capacity", "description", "is_active"]
    template_name = "gyms/gym_create_update.html"
    success_url = reverse_lazy("gyms:gym-list")
    permission_required = "gym.add_gym"


class GymUpdateView(PermissionRequiredMixin, UpdateView):
    model = Gym
    fields = ["name", "address", "capacity", "description", "is_active"]
    template_name = "gyms/gym_create_update.html"
    success_url = reverse_lazy("gyms:gym-list")
    permission_required = "gym.change_gym"


class GymDeleteView(PermissionRequiredMixin, DeleteView):
    model = Gym
    template_name = "gyms/gym_session_confirm_delete.html"
    success_url = reverse_lazy("gyms:gym-list")
    permission_required = "gym.delete_gym"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.model_name
        return context


class ToggleGymStatusView(View):
    def post(self, request, pk):
        gym = get_object_or_404(Gym, id=pk)
        gym.is_active = not gym.is_active
        gym.save()
        return redirect("gyms:gym-list")


class WorkoutSessionListView(LoginRequiredMixin, ListView):
    model = WorkoutSession
    template_name = "gyms/session_list.html"
    context_object_name = "sessions"
    paginate_by = 4

    def get_queryset(self):
        gym_id = self.kwargs["gym_pk"]
        return WorkoutSession.objects.filter(gym_id=gym_id).select_related(
            "trainer", "gym"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gym"] = get_object_or_404(Gym, pk=self.kwargs["gym_pk"])
        return context


class WorkoutSessionDetailView(LoginRequiredMixin, DetailView):
    model = WorkoutSession
    template_name = "gyms/session_detail.html"
    context_object_name = "session"

    def get_queryset(self):
        return (
            WorkoutSession.objects.annotate(
                _paid_bookings_count=Count("bookings", filter=Q(bookings__is_paid=True))
            )
            .prefetch_related(
                Prefetch(
                    "bookings",
                    queryset=Booking.objects.select_related("user"),
                    to_attr="bookings_with_users"
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.object

        context["description"] = session.description
        context["coach"] = session.trainer.username
        context["available_spots"] = session.get_available_spots()
        context["is_fully_booked"] = session.is_fully_booked()
        context["is_active"] = session.is_active
        context["has_ended"] = session.end_time < timezone.now()

        return context


class WorkoutSessionCreateView(LoginRequiredMixin, CreateView):
    model = WorkoutSession
    form_class = WorkoutSessionForm
    template_name = "gyms/session_create_update.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["gym"] = get_object_or_404(Gym, pk=self.kwargs.get("gym_pk"))
        return kwargs

    def form_valid(self, form):
        form.instance.gym = form.gym
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "gyms:workout-session-list",
            kwargs={"gym_pk": self.kwargs.get("gym_pk")},
        )


class WorkoutSessionUpdateView(
    LoginRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = WorkoutSession
    form_class = WorkoutSessionForm
    template_name = "gyms/session_create_update.html"

    def test_func(self):
        session = self.get_object()
        user = self.request.user
        return user.is_authenticated and (
            user.role in User.Roles.ADMIN
            or user.is_superuser
            or (user.role == User.Roles.TRAINER and session.trainer == user)
        )

    def get_success_url(self):
        return reverse_lazy(
            "gyms:workout-session-detail", kwargs={"pk": self.get_object().pk}
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.gym = self.get_object().gym

        if self.request.user.role == User.Roles.TRAINER:
            form.instance.trainer = self.request.user

        return super().form_valid(form)


class WorkoutSessionDeleteView(
    LoginRequiredMixin, UserPassesTestMixin, DeleteView
):
    model = WorkoutSession
    template_name = "gyms/gym_session_confirm_delete.html"

    def test_func(self):
        session = self.get_object()
        user = self.request.user
        return user.is_authenticated and (
                user.role in User.Roles.ADMIN
                or user.is_superuser
                or (user.role == User.Roles.TRAINER and session.trainer == user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.model_name
        return context

    def get_success_url(self):
        return reverse_lazy(
            "gyms:workout-session-list",
            kwargs={"gym_pk": self.get_object().gym.pk},
        )
