from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created"""
    if created:
        # Check if profile doesn't already exist
        if not hasattr(instance, 'profile'):
            try:
                UserProfile.objects.create(user=instance)
            except Exception as e:
                print(f"Error creating profile: {e}") 