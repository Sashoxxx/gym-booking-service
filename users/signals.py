from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Account


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_account(sender, instance, raw, created, **kwargs):
    if raw:
        return

    if created:
        Account.objects.create(
            user=instance,
            account_type='user',
            balance=0
        )
