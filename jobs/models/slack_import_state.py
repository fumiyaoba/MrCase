from django.db import models


class SlackImportState(models.Model):
    last_ts = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Slack取込状態"

    def __str__(self):
        return f"last_ts={self.last_ts}"
