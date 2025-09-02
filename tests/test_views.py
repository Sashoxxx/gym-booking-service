from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from users.models import CustomUser
from gym.models import Gym, WorkoutSession

class GymViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_user(username="admin", password="pass", role="admin")
        self.trainer = CustomUser.objects.create_user(username="trainer", password="pass", role="trainer")
        self.client_user = CustomUser.objects.create_user(username="client", password="pass", role="client")
        self.gym = Gym.objects.create(name="Gym A", address="Street", capacity=50)

    def test_gym_list_view(self):
        response = self.client.get(reverse("gyms:gym-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("gyms", response.context)

    def test_gym_detail_view(self):
        url = reverse("gyms:gym-detail", kwargs={"pk": self.gym.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["gym"], self.gym)

    def test_toggle_gym_status_view(self):
        self.client.force_login(self.admin)
        url = reverse("gyms:gym-toggle-status", kwargs={"pk": self.gym.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("gyms:gym-list"))
        self.gym.refresh_from_db()
        self.assertFalse(self.gym.is_active)

class WorkoutSessionViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.trainer = CustomUser.objects.create_user(username="trainer", password="pass", role="trainer")
        self.client_user = CustomUser.objects.create_user(username="client", password="pass", role="client")
        self.gym = Gym.objects.create(name="Gym A", address="Street", capacity=50)
        self.session = WorkoutSession.objects.create(
            title="Yoga",
            description="Morning",
            gym=self.gym,
            trainer=self.trainer,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            price=10
        )

    def test_session_list_view(self):
        self.client.force_login(self.client_user)
        url = reverse("gyms:workout-session-list", kwargs={"gym_pk": self.gym.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("sessions", response.context)

    def test_session_detail_view(self):
        self.client.force_login(self.client_user)
        url = reverse(
            "gyms:workout-session-detail",
            kwargs={
                "gym_pk": self.session.gym.pk,
                "pk": self.session.pk
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["session"], self.session)

    def test_session_create_view(self):
        self.client.force_login(self.trainer)
        url = reverse("gyms:workout-session-create", kwargs={"gym_pk": self.gym.pk})
        data = {
            "title": "Pilates",
            "description": "Evening",
            "start_time": timezone.now(),
            "end_time": timezone.now() + timezone.timedelta(hours=1),
            "price": 15,
            "max_participants": 10,
            "trainer": self.trainer.pk
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(WorkoutSession.objects.filter(title="Pilates").exists())

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_superuser(username="admin", password="pass", email="a@b.com")
        self.client_user = CustomUser.objects.create_user(username="client", password="pass", role="client")

    def test_user_list_view_permission(self):
        self.client.force_login(self.admin)
        url = reverse("users:user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.context)

    def test_user_detail_view_context(self):
        self.client.force_login(self.client_user)
        url = reverse("users:user-detail", kwargs={"pk": self.client_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["profile_user"], self.client_user)
        self.assertIn("account_balance", response.context)

    def test_add_balance_view(self):
        self.client.force_login(self.client_user)
        url = reverse("users:add-balance")
        response = self.client.post(url, {"amount": 50})
        self.assertEqual(response.status_code, 302)
        self.client_user.account.refresh_from_db()
        self.assertEqual(self.client_user.account.balance, 50)
