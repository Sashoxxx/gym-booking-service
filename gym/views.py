from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db import transaction
from django.db.models import Prefetch, Q
from django.db.models.aggregates import Count
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView,
    UpdateView,
    CreateView,
)

from gym.forms import WorkoutSessionForm
from gym.models import Gym, WorkoutSession, Booking
from users.models import Account


def index(request: HttpRequest) -> HttpResponse:
    """
    Handles the display of the index page by retrieving and calculating gym-related
    statistics and storing session information about the number of user visits.

    Parameters:
    request (HttpRequest): The HTTP request object containing metadata about
    the request.

    Returns:
    HttpResponse: The HTTP response object rendering the "gyms/index.html"
    template with the context data.

    Raises:
    None
    """
    num_visits = request.session.get("num_visits", 1)
    request.session["num_visits"] = num_visits + 1
    num_gyms = Gym.objects.count()
    total_trainers = (
        WorkoutSession.objects.values("trainer").distinct().count()
    )
    total_clients = Booking.objects.values("user").distinct().count()

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
        context["model_name"] = self.model._meta.model_name
        return context


def toggle_gym_status(request, pk):
    gym = get_object_or_404(Gym, id=pk)
    gym.is_active = not gym.is_active
    gym.save()
    return redirect("gyms:gym-list")


class WorkoutSessionListView(LoginRequiredMixin, ListView):
    model = WorkoutSession
    template_name = "gyms/session_list.html"
    context_object_name = "sessions"

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
            user.role in ["admin"]
            or user.is_superuser
            or (user.role == "trainer" and session.trainer == user)
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

        if self.request.user.role == "trainer":
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
            user.role in ["admin"]
            or user.is_superuser
            or (user.role == "trainer" and session.trainer == user)
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


class BookWorkoutSessionView(LoginRequiredMixin, View):
    """
    Handle booking process for workout sessions.

    The class provides GET and POST methods to manage the workflow for displaying
    a booking confirmation page and processing the booking of workout sessions.
    It ensures that only clients can book sessions and enforces various business
    rules, such as session availability, overlapping bookings, and sufficient
    funds for payment. The class also handles user feedback through messages
    and redirects as needed during the process.

    Methods:
        get: Displays the booking confirmation page, checking user eligibility
             and session availability.
        post: Processes the booking request, performs payment transactions, and
              updates booking and account information.
    """
    def get(self, request, session_id):
        """
        Display booking confirmation page.
        """
        user = request.user

        if user.role != "client":
            session = get_object_or_404(WorkoutSession, id=session_id)
            messages.error(request, "Only clients can book workout sessions.")
            return redirect(
                "gyms:workout-session-list", gym_pk=session.gym.pk
            )

        try:
            session = get_object_or_404(WorkoutSession, id=session_id)

            now = timezone.now()
            if now > session.end_time:
                messages.error(
                    request, "This workout session has already ended."
                )
                return redirect(
                    "gyms:workout-session-list", gym_pk=session.gym.pk
                )

            if session.is_fully_booked():
                messages.error(
                    request, "This workout session is fully booked."
                )
                return redirect(
                    "gyms:workout-session-list", gym_pk=session.gym.pk
                )

            overlapping_booking = Booking.objects.filter(
                user=user,
                session__start_time__lt=session.end_time,
                session__end_time__gt=session.start_time,
                is_paid=True,
            ).exists()

            if overlapping_booking:
                messages.error(
                    request,
                    "You already have another session booked at this time.",
                )
                return redirect(
                    "gyms:workout-session-list", gym_pk=session.gym.pk
                )

            existing_booking = Booking.objects.filter(
                user=user, session=session
            ).first()

            try:
                user_account = Account.objects.get(user=user)
            except Account.DoesNotExist:
                messages.error(
                    request, "User account not found. Please contact support."
                )
                return redirect(
                    "gyms:workout-session-list", gym_pk=session.gym.pk
                )

            context = {
                "session": session,
                "user_account": user_account,
                "existing_booking": existing_booking,
                "has_sufficient_funds": user_account.balance >= session.price,
                "available_spots": session.get_available_spots(),
            }

            return render(request, "gyms/book_session.html", context)

        except WorkoutSession.DoesNotExist:
            raise Http404("Workout session not found")

    def post(self, request, session_id):
        user = request.user

        if user.role != "client":
            messages.error(request, "Only clients can book workout sessions.")
            try:
                session = WorkoutSession.objects.get(id=session_id)
                return redirect("workout-session-list", gym_pk=session.gym.pk)
            except WorkoutSession.DoesNotExist:
                return redirect("gyms:book-session", session_id=session_id)

        try:
            with transaction.atomic():
                session = WorkoutSession.objects.select_for_update().get(
                    id=session_id
                )

                now = timezone.now()
                if now > session.end_time:
                    messages.error(
                        request, "This workout session has already ended."
                    )
                    return redirect(
                        "gyms:workout-session-list", gym_pk=session.gym.pk
                    )

                available_spots = session.get_available_spots()
                if available_spots <= 0:
                    messages.error(
                        request, "This workout session is fully booked."
                    )
                    return redirect(
                        "gyms:workout-session-list", gym_pk=session.gym.pk
                    )

                existing_booking = Booking.objects.filter(
                    user=user, session=session
                ).first()

                if existing_booking:
                    if existing_booking.is_paid:
                        messages.warning(
                            request,
                            "You have already booked "
                            "and paid for this session.",
                        )
                        return redirect(
                            "gyms:workout-session-detail",
                            gym_pk=session.gym.pk,
                            pk=session.pk,
                        )
                    else:
                        booking = existing_booking
                else:
                    booking = Booking(user=user, session=session)
                    booking.save()

                user_account = Account.objects.select_for_update().get(
                    user=user
                )
                gym_account = Account.objects.select_for_update().get(
                    gym=session.gym
                )

                if user_account.balance < session.price:
                    messages.error(
                        request,
                        f"Insufficient balance. You need {session.price} $ "
                        f"but have {user_account.balance} $.",
                    )
                    return redirect(
                        "gyms:book-session", session_id=session_id
                    )

                payment_successful = user_account.spend_money(session.price)
                if not payment_successful:
                    messages.error(
                        request, "Payment failed due to insufficient funds."
                    )
                    return redirect(
                        "gyms:book-session", session_id=session_id
                    )

                gym_account.add_money(session.price)

                booking.is_paid = True
                booking.paid_at = timezone.now()
                booking.save()

                messages.success(
                    request,
                    f"Successfully booked '{session.title}' "
                    f"for {session.price} $. "
                    f"Your remaining balance: {user_account.balance} $.",
                )
                return redirect("gyms:booking-success", booking_id=booking.id)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect("gyms:book-session", session_id=session_id)

        except WorkoutSession.DoesNotExist:
            messages.error(request, "Workout session not found.")
            return redirect("gyms:book-session", session_id=session_id)

        except Account.DoesNotExist:
            messages.error(
                request, "Account not found. Please contact support."
            )
            return redirect("gyms:book-session", session_id=session_id)

        except Exception as e:
            messages.error(
                request,
                f"An error occurred while processing your booking: {str(e)}",
            )
            return redirect("gyms:workout-sessions-list")


def booking_success_view(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    context = {
        "booking": booking,
        "session": booking.session,
        "gym": booking.session.gym,
    }

    return render(request, "gyms/booking_success.html", context)
