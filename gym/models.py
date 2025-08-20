from django.core.exceptions import ValidationError
from django.db import models

from config import settings


class Gym(models.Model):
    """
    Represents a gym entity in the application.

    The Gym class is designed to store and manage details about a specific gym, such
    as its name, address, capacity, and other related information. This data is crucial
    for organizing and maintaining gym-related records.

    :ivar name: The name of the gym.
    :type name: str
    :ivar address: The physical address of the gym.
    :type address: str
    :ivar capacity: The maximum number of people the gym can accommodate.
    :type capacity: int
    :ivar description: An optional detailed description of the gym.
    :type description: str or None
    :ivar is_active: Indicates whether the gym is currently active.
    :type is_active: bool
    :ivar created_at: The timestamp when the gym was added to the system.
    :type created_at: datetime.datetime
    """
    name = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.PositiveIntegerField()
    staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="gyms",
        limit_choices_to={"role": ("trainer", "admin")},
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class WorkoutSession(models.Model):
    """
    Represents a session for a workout, managed within a gym context.

    Provides functionality to manage, validate, and determine session status,
    such as availability, bookings, and whether the session is fully booked.
    Each workout session is associated with a gym and a trainer.

    :ivar title: The title of the workout session.
    :type title: str
    :ivar description: Detailed description of the workout session.
    :type description: str
    :ivar gym: Reference to the associated gym for the session.
    :type gym: Gym
    :ivar trainer: The trainer conducting the session, restricted to users
        with a "trainer" role.
    :type trainer: AUTH_USER_MODEL
    :ivar start_time: The start time of the workout session.
    :type start_time: datetime
    :ivar end_time: The end time of the workout session.
    :type end_time: datetime
    :ivar price: The cost of attending the workout session.
    :type price: int
    :ivar max_participants: The maximum number of participants allowed in the
        session. Defaults to 10.
    :type max_participants: int
    :ivar is_active: Indicates whether the session is open for bookings.
        Defaults to True.
    :type is_active: bool
    :ivar created_at: The timestamp when the session was created.
    :type created_at: datetime
    """
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
        related_name="sessions",
        limit_choices_to={"role": "trainer"},
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    price = models.PositiveIntegerField()
    max_participants = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_available_spots(self):
        booked_count = self.bookings.filter(is_paid=True).count()
        return self.max_participants - booked_count

    def is_fully_booked(self):
        return self.get_available_spots() <= 0

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Time period must start before it ends")

        if self.max_participants > self.gym.capacity:
            raise ValidationError("Maximum number of participants cannot exceed gym capacity")

    def __str__(self):
        return f"{self.title} - {self.gym.name} ({self.start_time.strftime('%d.%m.%Y %H:%M')})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["start_time"]


class Booking(models.Model):
    """
    Represents a booking made by a user for a specific workout session.

    This class is used to store and manage data pertaining to a client's booking for a workout session.
    It includes relevant information about the user, session, payment status, and timestamps.
    Additionally, it ensures no duplicate bookings for the same user and session combination can exist.

    :ivar user: The user who made the booking. Only users with the role of 'client' are valid.
    :type user: ForeignKey
    :ivar session: The workout session that the user has booked.
    :type session: ForeignKey
    :ivar is_paid: Indicates whether the booking has been paid for. Defaults to False.
    :type is_paid: bool
    :ivar created_at: The timestamp when the booking was created.
    :type created_at: DateTimeField
    :ivar paid_at: The timestamp when the booking was paid, if applicable. Optional.
    :type paid_at: DateTimeField
    """
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата оплати")


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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ["user", "session"]
        ordering = ["-created_at"]

