from django.contrib import admin
from jobs.models import Case, ManHourRecord


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "created_by", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ManHourRecord)
class ManHourRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "work_date", "project_name", "assignee", "hours", "source_ts", "created_at")
    list_filter = ("work_date", "assignee")
    search_fields = ("project_name", "assignee")
    date_hierarchy = "work_date"
