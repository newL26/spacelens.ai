"""
Accounts models — extended user profile.
One-to-one with Django's built-in User via a post_save signal.
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )
    organisation = models.CharField(max_length=120, blank=True)
    bio = models.TextField(max_length=400, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} — Profile"

    @property
    def display_name(self) -> str:
        return self.user.get_full_name() or self.user.username

    @property
    def initials(self) -> str:
        full = self.user.get_full_name()
        if full:
            parts = full.split()
            return (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else parts[0][0].upper()
        return self.user.username[0].upper()


# ── Auto-create profile when a User is created ────────────────────────────────
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
