from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from gym.models import Gym


class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        CLIENT = "client", "Client"
        TRAINER = "trainer", "Trainer"
        ADMIN = "admin", "Admin"

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(
            r"^\+?\d{9,15}$",
            "Enter a valid phone number.",
        )],
    )
    role = models.CharField(
        max_length=10,
        choices=Roles,
        default=Roles.CLIENT
    )
    email = models.EmailField(
        blank=True,
        unique=True,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Account(models.Model):
    class Types(models.TextChoices):
        GYM = "gym", "Gym"
        USER = "user", "User"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account",
        blank=True,
        null=True
    )
    gym = models.OneToOneField(
        Gym,
        on_delete=models.CASCADE,
        related_name="account",
        blank=True,
        null=True
    )
    account_type = models.CharField(
        max_length=10,
        choices=Types
    )
    balance = models.PositiveIntegerField(
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def add_money(self, amount: int) -> None:
        if amount > 0:
            self.balance += amount
            self.save()
        else:
            raise ValueError("Amount must be positive")

    def spend_money(self, amount: int) -> bool:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    def clean(self):
        if (self.user and self.gym) or (not self.user and not self.gym):
            raise ValueError(
                "Account must have either a user or a gym"
            )
        if self.user:
            self.account_type = "user"
        elif self.gym:
            self.account_type = "gym"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_account_type_display()} have {self.balance}"
