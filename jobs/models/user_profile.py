from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    slack_user_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Slack メンバーID",
    )

    class Meta:
        verbose_name = "ユーザープロフィール"

    def __str__(self):
        return f"{self.user.username} profile"
