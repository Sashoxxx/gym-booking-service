from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import CustomUser
from gym.models import Gym, WorkoutSession, Booking

class GymModelTest(TestCase):
    def test_gym_str(self):
        gym = Gym.objects.create(name="Test Gym", address="123 Street", capacity=50)
        self.assertEqual(str(gym), "Test Gym")

class WorkoutSessionModelTest(TestCase):
    def test_workout_session_str(self):
        gym = Gym.objects.create(name="Gym A", address="Street", capacity=50)
        trainer = CustomUser.objects.create_user(username="trainer", password="pass", role="trainer")
        session = WorkoutSession.objects.create(
            title="Yoga",
            description="Morning Yoga",
            gym=gym,
            trainer=trainer,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            price=10
        )
        self.assertIn("Yoga - Gym A", str(session))

class BookingModelTest(TestCase):
    def test_booking_unique_validation(self):
        gym = Gym.objects.create(name="Gym A", address="Street", capacity=50)
        trainer = CustomUser.objects.create_user(username="trainer", password="pass", role="trainer")
        client = CustomUser.objects.create_user(username="client", password="pass", role="client")
        session = WorkoutSession.objects.create(
            title="Yoga",
            description="Morning Yoga",
            gym=gym,
            trainer=trainer,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            price=10
        )
        Booking.objects.create(user=client, session=session)
        duplicate_booking = Booking(user=client, session=session)
        with self.assertRaises(ValidationError):
            duplicate_booking.full_clean()

class AccountModelTest(TestCase):
    def test_account_creation_signal(self):
        user = CustomUser.objects.create_user(username="client", password="pass", role="client")
        self.assertTrue(hasattr(user, "account"))

    def test_account_methods(self):
        user = CustomUser.objects.create_user(username="client2", password="pass", role="client")
        account = user.account
        account.add_money(50)
        self.assertEqual(account.balance, 50)
        self.assertTrue(account.spend_money(20))
        self.assertEqual(account.balance, 30)
        self.assertFalse(account.spend_money(50))
