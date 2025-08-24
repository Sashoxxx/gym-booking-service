from django.db.models.signals import post_save
from django.dispatch import receiver


from users.models import Account
from gym.models import Gym


@receiver(post_save, sender=Gym)
def create_gym_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.get_or_create(
            gym=instance,
            account_type='gym',
            balance=0
        )
