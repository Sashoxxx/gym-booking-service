from django.contrib.auth.models import AbstractUser
from django.db import models

from config import settings
from gym.models import Gym


class CustomUser(AbstractUser):
    """
    Represents a custom user in the system.

    This class extends the default Django AbstractUser by adding additional
    fields and functionality specific to the application's requirements.
    It allows users to have a defined role and an optional phone number.

    :ivar phone_number: An optional phone number associated with the user.
    :type phone_number: str
    :ivar role: The role assigned to the user. Default is 'client'.
    :type role: str
    """
    class Roles(models.TextChoices):
        CLIENT = "client", "Client"
        TRAINER = "trainer", "Trainer"
        ADMIN = "admin", "Admin"

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )
    role = models.CharField(
        max_length=10,
        choices=Roles,
        default=Roles.CLIENT)


    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Account(models.Model):
    """
    Represents an Account model that serves as a financial entity for either a user or a gym.

    This model is designed to connect a user or a gym with account-related functionalities,
    including managing balance and enforcing certain validation rules. The account type is 
    automatically determined based on the related entity (user or gym).

    :ivar user: A one-to-one relationship to the authenticated user model. Can be null.
    :type user: models.OneToOneField
    :ivar gym: A one-to-one relationship to a gym instance. Can be null.
    :type gym: models.OneToOneField
    :ivar account_type: The type of the account; can be either "user" or "gym".
    :type account_type: models.CharField
    :ivar balance: The current balance of the account in integer format.
    :type balance: models.PositiveIntegerField
    :ivar created_at: The timestamp indicating when the account was created.
    :type created_at: models.DateTimeField
    
    """
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
