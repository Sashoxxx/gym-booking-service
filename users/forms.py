from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

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
        model = User
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
        if role == User.Roles.CLIENT:
            raise forms.ValidationError("Can create only staff users")
        return role

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields +(
            "first_name",
            "last_name",
            "email",
            "phone_number",
        )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
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
