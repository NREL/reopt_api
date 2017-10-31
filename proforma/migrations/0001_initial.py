# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-31 21:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('reo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProForma',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
                ('spreadsheet_created', models.DateTimeField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('scenario_model', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='reo.ScenarioModel')),
            ],
        ),
    ]
