from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UserPassesTestMixin
)
from django.db.models import Prefetch
from django.db.models.aggregates import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView

from gym.forms import WorkoutSessionForm
from gym.models import Gym, WorkoutSession, Booking


def index(request: HttpRequest) -> HttpResponse:
    num_visits = request.session.get("num_visits", 1)
    request.session["num_visits"] = num_visits + 1
    gyms = Gym.objects.all()

    num_gyms = gyms.count()

    total_trainers = gyms.aggregate(
        total=Count(
            'sessions__trainer', distinct=True
        )
    )['total']
    total_clients = gyms.aggregate(
        total=Count(
            'sessions__clients', distinct=True
        )
    )['total']

    context = {
        "num_gyms": num_gyms,
        "total_trainers": total_trainers,
        "total_clients": total_clients,
        "num_visits": num_visits,
    }
    return render(request, "gyms/index.html", context)

class GymListView(ListView):
    model = Gym
    template_name = "gyms/gym_list.html"
    context_object_name = "gyms"

    def get_queryset(self):
        return Gym.objects.all().prefetch_related("sessions")


class GymDetailView(DetailView):
    model = Gym
    template_name = "gyms/gym_detail.html"
    context_object_name = "gym"

    def get_queryset(self):
        return Gym.objects.all().prefetch_related("sessions")


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
        context['model_name'] = self.model._meta.model_name
        return context

class WorkoutSessionListView(LoginRequiredMixin, ListView):
    model = WorkoutSession
    template_name = "gyms/session_list.html"
    context_object_name = "sessions"

    def get_queryset(self):
        gym_id = self.kwargs["gym_pk"]
        return WorkoutSession.objects.filter(
            gym_id=gym_id
        ).select_related("trainer", "gym")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gym"] = get_object_or_404(Gym, pk=self.kwargs["gym_pk"])
        return context


class WorkoutSessionDetailView(LoginRequiredMixin, DetailView):
    model = WorkoutSession
    template_name = "gyms/session_detail.html"
    context_object_name = "session"

    def get_queryset(self):
        return WorkoutSession.objects.prefetch_related(
            Prefetch(
                "bookings",
                queryset=Booking.objects.select_related("user"),
                to_attr="bookings_with_users"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.object

        context["available_spots"] = session.get_available_spots()
        context["is_fully_booked"] = session.is_fully_booked()
        context["is_active"] = session.is_active

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
        return reverse_lazy("gyms:workout-session-list", kwargs={"gym_pk": self.kwargs.get("gym_pk")})



class WorkoutSessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WorkoutSession
    form_class = WorkoutSessionForm
    template_name = "gyms/session_create_update.html"


    def test_func(self):
        session = self.get_object()
        user = self.request.user
        return user.is_authenticated and (
            user.role in ["admin"] or user.is_superuser or (user.role == "trainer" and session.trainer == user)
        )

    def get_success_url(self):
        return reverse_lazy("gyms:workout-session-detail", kwargs={"pk": self.get_object().pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.gym = self.get_object().gym

        if self.request.user.role == "trainer":
            form.instance.trainer = self.request.user

        return super().form_valid(form)

class WorkoutSessionDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    model = WorkoutSession
    template_name = "gyms/gym_session_confirm_delete.html"
    success_url = reverse_lazy("gyms:sessions-list")
