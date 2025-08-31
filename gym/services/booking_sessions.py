from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from gym.models import WorkoutSession, Booking
from users.models import Account

User = get_user_model()

class BookWorkoutSessionView(LoginRequiredMixin, View):
    def get(self, request, session_id):
        user = request.user
        if user.role != User.Roles.CLIENT:
            messages.error(request, "Only clients can book workout sessions.")
            session = get_object_or_404(WorkoutSession, id=session_id)
            return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

        session = get_object_or_404(WorkoutSession, id=session_id)
        now = timezone.now()

        if now > session.end_time:
            messages.error(request, "This workout session has already ended.")
            return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

        if session.is_fully_booked():
            messages.error(request, "This workout session is fully booked.")
            return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

        overlapping_booking = Booking.objects.filter(
            user=user,
            session__start_time__lt=session.end_time,
            session__end_time__gt=session.start_time,
            is_paid=True,
        ).exists()

        existing_booking = Booking.objects.filter(user=user, session=session).first()

        try:
            user_account = Account.objects.get(user=user)
        except Account.DoesNotExist:
            messages.error(request, "User account not found. Please contact support.")
            return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

        context = {
            "session": session,
            "user_account": user_account,
            "existing_booking": existing_booking,
            "has_sufficient_funds": user_account.balance >= session.price,
            "available_spots": session.get_available_spots(),
            "can_book": not overlapping_booking,
        }

        if overlapping_booking:
            messages.warning(request, "You already have another session booked at this time.")

        return render(request, "gyms/book_session.html", context)

    def post(self, request, session_id):
        user = request.user
        if user.role != User.Roles.CLIENT:
            messages.error(request, "Only clients can book workout sessions.")
            session = get_object_or_404(WorkoutSession, id=session_id)
            return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

        try:
            with transaction.atomic():
                session = WorkoutSession.objects.select_for_update().get(id=session_id)
                now = timezone.now()

                if now > session.end_time:
                    messages.error(request, "This workout session has already ended.")
                    return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

                if session.get_available_spots() <= 0:
                    messages.error(request, "This workout session is fully booked.")
                    return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

                overlapping_booking = Booking.objects.filter(
                    user=user,
                    session__start_time__lt=session.end_time,
                    session__end_time__gt=session.start_time,
                    is_paid=True,
                ).exists()
                if overlapping_booking:
                    messages.error(request, "You already have another session booked at this time.")
                    return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)

                existing_booking = Booking.objects.filter(user=user, session=session).first()
                if existing_booking:
                    booking = existing_booking

                    booking.canceled_at = None
                    booking.save(update_fields=["canceled_at"])
                else:
                    booking = Booking(user=user, session=session)
                    booking.save()

                user_account = Account.objects.select_for_update().get(user=user)
                gym_account = Account.objects.select_for_update().get(gym=session.gym)

                if user_account.balance < session.price:
                    messages.error(
                        request,
                        f"Insufficient balance. You need {session.price}$ but have {user_account.balance}$."
                    )
                    return redirect("gyms:book-session", session_id=session_id)

                if not user_account.spend_money(session.price):
                    messages.error(request, "Payment failed due to insufficient funds.")
                    return redirect("gyms:book-session", session_id=session_id)

                gym_account.add_money(session.price)

                booking.is_paid = True
                booking.paid_at = now
                booking.save()

                messages.success(
                    request,
                    f"Successfully booked '{session.title}' for {session.price}$. "
                    f"Your remaining balance: {user_account.balance}$."
                )
                return redirect("gyms:booking-success", booking_id=booking.id)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("gyms:workout-session-list", gym_pk=session.gym.pk)


def booking_success_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    context = {
        "booking": booking,
        "session": booking.session,
        "gym": booking.session.gym,
    }

    return render(request, "gyms/booking_success.html", context)


class CancelBookingView(View):
    template_name = "gyms/cancel_booking_confirm.html"

    @staticmethod
    def get_booking(booking_id, user):
        return get_object_or_404(
            Booking.objects.select_for_update()
            .select_related("user__account", "session__gym__account"),
            pk=booking_id,
            user=user,
            is_paid=True
        )

    def _check_cancellation_allowed(self, booking):
        delta_hours = (booking.session.start_time - timezone.now()).total_seconds() / 3600
        if delta_hours < 0:
            messages.error(self.request, "⚠️ Session already started, cancellation is not possible")
            return False, delta_hours
        return True, delta_hours

    def get(self, request, booking_id):
        self.request = request
        booking = self.get_booking(booking_id, request.user)
        allowed, delta_hours = self._check_cancellation_allowed(booking)
        if not allowed:
            return redirect("users:user-detail", pk=request.user.pk)

        return render(
            request,
            self.template_name,
            {
                "booking": booking,
                "full_refund": delta_hours >= 2
            }
        )

    def post(self, request, booking_id):
        self.request = request
        booking = self.get_booking(booking_id, request.user)
        allowed, delta_hours = self._check_cancellation_allowed(booking)
        if not allowed:
            return redirect("users:user-detail", pk=request.user.pk)

        now = timezone.now()
        user_account = booking.user.account
        gym_account = booking.session.gym.account

        with transaction.atomic():
            if delta_hours >= 2:
                gym_account.spend_money(booking.session.price)
                user_account.add_money(booking.session.price)
                messages.success(request, "✅ Cancellation successful with full refund")
            else:
                messages.warning(request, "❌ Cancellation successful without refund")

            booking.is_paid = False
            booking.canceled_at = now
            booking.save(update_fields=["is_paid", "canceled_at"])

        return redirect("users:user-detail", pk=request.user.pk)
