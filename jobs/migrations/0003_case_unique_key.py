import secrets
import string

from django.db import migrations, models


def generate_unique_key():
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))


def fill_unique_keys(apps, schema_editor):
    """既存レコードに重複しないキーを1件ずつ割り当てる"""
    Case = apps.get_model("jobs", "Case")
    used = set()
    for case in Case.objects.all():
        key = generate_unique_key()
        while key in used or Case.objects.filter(unique_key=key).exists():
            key = generate_unique_key()
        case.unique_key = key
        case.save(update_fields=["unique_key"])
        used.add(key)


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_manhourrecord"),
    ]

    operations = [
        # まず unique なしでカラム追加
        migrations.AddField(
            model_name="case",
            name="unique_key",
            field=models.CharField(max_length=8, default="TMP00000"),
            preserve_default=False,
        ),
        # 既存レコードにユニークなキーを埋める
        migrations.RunPython(fill_unique_keys, migrations.RunPython.noop),
        # unique 制約を付与
        migrations.AlterField(
            model_name="case",
            name="unique_key",
            field=models.CharField(max_length=8, unique=True),
        ),
    ]
