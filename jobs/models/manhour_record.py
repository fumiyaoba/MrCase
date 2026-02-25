from django.db import models
from jobs.models.case import Case


class ManHourRecord(models.Model):
    case = models.ForeignKey(
        Case,
        on_delete=models.PROTECT,
        related_name="manhour_records",
        null=True,
        blank=True,
    )
    # Slackメッセージの案件名（case が見つからない場合も保持）
    project_name = models.CharField(max_length=200)
    assignee = models.CharField(max_length=200)
    work_date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)

    # Slack message の ts（重複登録防止）
    source_ts = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-work_date", "assignee"]

    def __str__(self):
        return f"{self.work_date} | {self.project_name} | {self.assignee} | {self.hours}h"