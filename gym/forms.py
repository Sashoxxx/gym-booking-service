from django import forms
from django.contrib.auth import get_user_model

from gym.models import WorkoutSession


User = get_user_model()
class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = [
            "title",
            "description",
            "start_time",
            "end_time",
            "price",
            "max_participants",
            "trainer"
        ]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        self.gym = kwargs.pop("gym", None)
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.fields["trainer"].queryset = User.objects.filter(role="trainer")

        if user.role == User.Roles.TRAINER:
            self.fields["trainer"].widget = forms.HiddenInput()
            self.fields["trainer"].initial = user
            self.fields.pop("clients", None)
