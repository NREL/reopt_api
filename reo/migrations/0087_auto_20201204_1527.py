# Generated by Django 2.2.13 on 2020-12-04 22:27

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0086_auto_20201110_1618'),
    ]

    operations = [
        migrations.AddField(
            model_name='flextechacmodel',
            name='crankcase_power_kW',
            field=models.FloatField(blank=True, default=0.02, null=True),
        ),
        migrations.AddField(
            model_name='flextechacmodel',
            name='crankcase_temp_limit_degF',
            field=models.FloatField(blank=True, default=55.0, null=True),
        ),
        migrations.AddField(
            model_name='flextechacmodel',
            name='use_crankcase',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='flextechacmodel',
            name='year_one_crankcase_power_consumption_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, null=True, size=None),
        ),
    ]
