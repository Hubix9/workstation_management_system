# Generated by Django 5.0.1 on 2024-04-06 14:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workstation_coordinator', '0010_alter_workstation_additional_information'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workstation',
            name='name',
        ),
    ]
