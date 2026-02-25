import secrets
import string

from django.db import models
from django.conf import settings


def generate_unique_key():
    """8桁のランダムな英数字キーを生成"""
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))


class Case(models.Model):
    name = models.CharField(max_length=200)
    unique_key = models.CharField(max_length=8, unique=True, default=generate_unique_key)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_cases",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.unique_key}] {self.name}"