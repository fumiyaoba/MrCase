from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ManHourRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("project_name", models.CharField(max_length=200)),
                ("assignee", models.CharField(max_length=200)),
                ("work_date", models.DateField()),
                (
                    "hours",
                    models.DecimalField(decimal_places=2, max_digits=6),
                ),
                (
                    "source_ts",
                    models.CharField(max_length=50, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="manhour_records",
                        to="jobs.case",
                    ),
                ),
            ],
            options={
                "ordering": ["-work_date", "assignee"],
            },
        ),
    ]
