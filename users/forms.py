from django import forms
from django.contrib.auth.forms import UserCreationForm

from users.models import CustomUser


class UserSearchForm(forms.Form):
    ROLE_CHOICES = [
        ("", "All"),
        ("client", "Client"),
        ("trainer", "Trainer"),
        ("admin", "Admin"),
    ]
    search = forms.CharField(
        required=False,
        label="Search by",
        widget=forms.TextInput(
            attrs={
            "placeholder": "Username, email, first name",
            "class": "form-control"
            }
        )
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        label="Role",
        widget=forms.Select(attrs={"class": "form-control"})
    )

class StaffUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "phone_number",
            "role",
            "password1",
            "password2"
        )

    def clean_role(self):
        role = self.cleaned_data.get("role")
        if role == CustomUser.Roles.CLIENT:
            raise forms.ValidationError("Can create only staff users")
        return role

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password1",
            "password2"
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Roles.CLIENT
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number"
        )


class AddBalanceForm(forms.Form):
    amount = forms.IntegerField(
        min_value=1,
        label="Amount to add",
        help_text="Enter a positive number"
    )
