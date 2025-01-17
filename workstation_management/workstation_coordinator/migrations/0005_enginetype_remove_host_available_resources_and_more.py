# Generated by Django 5.0.1 on 2024-03-28 19:24

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workstation_coordinator', '0004_remove_proxymapping_external_address_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EngineType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='host',
            name='available_resources',
        ),
        migrations.RemoveField(
            model_name='host',
            name='engine',
        ),
        migrations.RemoveField(
            model_name='host',
            name='max_resources',
        ),
        migrations.RemoveField(
            model_name='host',
            name='port',
        ),
        migrations.RemoveField(
            model_name='template',
            name='allowed_engines',
        ),
        migrations.AddField(
            model_name='engine',
            name='available_resources',
            field=models.JSONField(default={}),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='engine',
            name='max_resources',
            field=models.JSONField(default={}),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='engine',
            name='port',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='host',
            name='engines',
            field=models.ManyToManyField(to='workstation_coordinator.engine'),
        ),
        migrations.AddField(
            model_name='template',
            name='internal_name',
            field=models.CharField(default='none', max_length=200, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='engine',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='workstation_coordinator.enginetype'),
        ),
        migrations.AddField(
            model_name='template',
            name='allowed_engine_types',
            field=models.ManyToManyField(to='workstation_coordinator.enginetype'),
        ),
    ]
