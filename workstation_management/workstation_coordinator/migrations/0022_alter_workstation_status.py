# Generated by Django 5.0.1 on 2024-06-16 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workstation_coordinator', '0021_alter_workstation_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workstation',
            name='status',
            field=models.CharField(choices=[('Cleanup', 'Cleanup'), ('Active', 'Active'), ('Setup', 'Setup'), ('Archived', 'Archived'), ('Scheduled', 'Scheduled'), ('Broken', 'Broken'), ('Restart', 'Restar')], default='Scheduled', max_length=200),
        ),
    ]