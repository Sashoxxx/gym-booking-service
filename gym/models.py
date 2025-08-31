from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(
        auto_now=True,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True


class Gym(TimestampMixin, models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.name


class WorkoutSession(TimestampMixin, models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_sessions",
        limit_choices_to={"role": "trainer"},
    )
    clients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="client_sessions",
        limit_choices_to={"role": "client"},
        through="Booking",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    price = models.PositiveIntegerField()
    max_participants = models.PositiveIntegerField(default=10)

    @property
    def is_active(self):

        now = timezone.now()
        if now > self.end_time:
            return False
        if self.is_fully_booked():
            return False
        return True

    @property
    def paid_bookings_count(self):
        return getattr(self, "_paid_bookings_count", self.bookings.filter(is_paid=True).count())

    def get_available_spots(self):
        return self.max_participants - self.paid_bookings_count

    def is_fully_booked(self):
        return self.get_available_spots() <= 0


    def __str__(self):
        gym_name = self.gym.name if self.gym else "No Gym"
        start_time_str = self.start_time.strftime('%d.%m.%Y %H:%M') if self.start_time else "No Time"
        return f"{self.title} - {gym_name} ({start_time_str})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["start_time"]


class Booking(TimestampMixin, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        limit_choices_to={"role": "client"},
    )
    session = models.ForeignKey(
        WorkoutSession,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)


    def clean(self):
        if self.pk is None:
            existing = Booking.objects.filter(
                user=self.user,
                session=self.session,
            ).exists()
            if existing:
                raise ValidationError("You have already booked this session")

    def __str__(self):
        status = "Paid" if self.is_paid else "Pending"

        return f"{self.user.username} - {self.session.title} ({status})"

    @property
    def is_canceled(self):
        return self.canceled_at is not None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ["user", "session"]
        ordering = ["-created_at"]
