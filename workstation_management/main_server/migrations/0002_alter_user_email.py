# Generated by Django 5.0.1 on 2024-02-07 23:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_server', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
