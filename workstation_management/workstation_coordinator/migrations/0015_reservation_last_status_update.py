# Generated by Django 5.0.1 on 2024-05-23 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workstation_coordinator', '0014_workstation_last_status_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='last_status_update',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
