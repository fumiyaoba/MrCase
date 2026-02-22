from django.db import models

class ManHourRecord(models.Model):
    project = models.CharField(max_length=200)
    assignee = models.CharField(max_length=200)
    work_date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)

    source_ts = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)