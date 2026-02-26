from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0004_alter_case_unique_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="SlackImportState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_ts", models.CharField(max_length=50)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Slack取込状態",
            },
        ),
    ]
