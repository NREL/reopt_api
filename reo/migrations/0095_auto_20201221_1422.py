# Generated by Django 2.2.13 on 2020-12-21 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0094_auto_20201217_1743'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HotWaterTankModel',
        ),
        migrations.RenameField(
            model_name='flextechwhmodel',
            old_name='temperature_setpoint_degC',
            new_name='installed_cost_us_dollars_per_kw',
        ),
        migrations.RenameField(
            model_name='flextechwhmodel',
            old_name='water_mains_temp_degC',
            new_name='year_one_temperature_series_degC',
        ),
        migrations.AddField(
            model_name='flextechwhmodel',
            name='temperature_lower_bound_degC',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flextechwhmodel',
            name='temperature_upper_bound_degC',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
