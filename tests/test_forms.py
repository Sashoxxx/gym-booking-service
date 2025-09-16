from django.test import TestCase
from django.utils import timezone
from users.models import CustomUser
from gym.models import Gym
from gym.forms import WorkoutSessionForm
from users.forms import CustomUserCreationForm, AddBalanceForm

class WorkoutSessionFormTest(TestCase):
    def test_workout_session_form_valid(self):
        trainer = CustomUser.objects.create_user(username="trainer1", password="pass", role="trainer")
        gym = Gym.objects.create(name="Gym A", address="Street", capacity=50)
        data = {
            "title": "Yoga",
            "description": "Morning",
            "start_time": timezone.now(),
            "end_time": timezone.now() + timezone.timedelta(hours=1),
            "price": 10,
            "max_participants": 10,
            "trainer": trainer.id
        }
        form = WorkoutSessionForm(data=data, user=trainer, gym=gym)
        self.assertTrue(form.is_valid())

class CustomUserCreationFormTest(TestCase):
    def test_custom_user_creation_form_valid(self):
        data = {"username":"user1","password1":"pass12345","password2":"pass12345","email":"a@b.com"}
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())

class AddBalanceFormTest(TestCase):
    def test_add_balance_form_valid(self):
        form = AddBalanceForm(data={"amount": 100})
        self.assertTrue(form.is_valid())
