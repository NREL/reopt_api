# Generated by Django 2.2.13 on 2021-01-15 17:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0106_auto_20210114_2103'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flextechacmodel',
            name='crankcase_power_kw',
        ),
        migrations.RemoveField(
            model_name='flextechacmodel',
            name='crankcase_temp_limit_degF',
        ),
        migrations.RemoveField(
            model_name='flextechacmodel',
            name='use_crankcase',
        ),
        migrations.RemoveField(
            model_name='flextechacmodel',
            name='year_one_crankcase_power_consumption_series_kw',
        ),
    ]
