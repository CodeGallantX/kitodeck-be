from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    Extended profile model for the Django User model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True)
    
    # Social media fields
    twitter = models.CharField(max_length=50, blank=True)
    linkedin = models.CharField(max_length=50, blank=True)
    github = models.CharField(max_length=50, blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

# Signal to create user profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Ensure profile exists
        Profile.objects.create(user=instance)