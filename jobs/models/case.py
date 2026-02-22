from django.db import models
from django.conf import settings

class Case(models.Model):
    name = models.CharField(max_length=200)               # 案件名
    description = models.TextField(blank=True)            # 説明（任意）
    is_active = models.BooleanField(default=True)         # 有効/無効
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_cases",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name