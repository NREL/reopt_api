# Generated by Django 2.2.13 on 2021-03-20 03:58

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0106_auto_20210315_0341'),
    ]

    operations = [
        migrations.CreateModel(
            name='MassProducerModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('run_uuid', models.UUIDField(unique=True)),
                ('mass_units', models.TextField(blank=True, null=True)),
                ('time_units', models.TextField(blank=True, null=True)),
                ('min_mass_per_time', models.FloatField(blank=True, null=True)),
                ('max_mass_per_time', models.FloatField(blank=True, null=True)),
                ('electric_consumed_to_mass_produced_ratio_kwh_per_mass', models.FloatField(blank=True, null=True)),
                ('thermal_consumed_to_mass_produced_ratio_kwh_per_mass', models.FloatField(blank=True, null=True)),
                ('feedstock_consumed_to_mass_produced_ratio', models.FloatField(blank=True, null=True)),
                ('installed_cost_us_dollars_per_mass_per_time', models.FloatField(blank=True, null=True)),
                ('om_cost_us_dollars_per_mass_per_time', models.FloatField(blank=True, null=True)),
                ('om_cost_us_dollars_per_mass', models.FloatField(blank=True, null=True)),
                ('mass_value_us_dollars_per_mass', models.FloatField(blank=True, null=True)),
                ('feedstock_cost_us_dollars_per_mass', models.FloatField(blank=True, null=True)),
                ('macrs_option_years', models.IntegerField(blank=True, null=True)),
                ('macrs_bonus_pct', models.FloatField(blank=True, null=True)),
                ('size_mass_per_time', models.FloatField(blank=True, null=True)),
                ('year_one_electric_consumption_kwh', models.FloatField(blank=True, null=True)),
                ('year_one_thermal_consumption_mmbtu', models.FloatField(blank=True, null=True)),
                ('year_one_mass_produced_mass', models.FloatField(blank=True, null=True)),
                ('year_one_feedstock_consumption_mass', models.FloatField(blank=True, null=True)),
                ('year_one_electric_consumption_series_kw', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None)),
                ('year_one_thermal_consumption_series_mmbtu_per_hr', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None)),
                ('year_one_mass_production_series_mass_per_hr', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None)),
                ('year_one_mass_value', models.FloatField(blank=True, null=True)),
                ('year_one_feedstock_cost', models.FloatField(blank=True, null=True)),
                ('total_mass_value', models.FloatField(blank=True, null=True)),
                ('total_feedstock_cost', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.RenameField(
            model_name='hottesmodel',
            old_name='year_one_thermal_from_hot_tes_series_mmbtu_per_hr',
            new_name='year_one_thermal_to_load_series_mmbtu_per_hr',
        ),
        migrations.AddField(
            model_name='boilermodel',
            name='can_supply_mp',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='boilermodel',
            name='year_one_thermal_to_massproducer_series_mmbtu_per_hr',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='chpmodel',
            name='can_supply_mp',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chpmodel',
            name='year_one_electric_to_massproducer_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='chpmodel',
            name='year_one_thermal_to_massproducer_series_mmbtu_per_hr',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='electrictariffmodel',
            name='year_one_to_massproducer_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='generatormodel',
            name='year_one_to_massproducer_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='hottesmodel',
            name='can_supply_mp',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hottesmodel',
            name='year_one_thermal_to_massproducer_series_mmbtu_per_hr',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='newboilermodel',
            name='can_supply_mp',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='newboilermodel',
            name='year_one_thermal_to_massproducer_series_mmbtu_per_hr',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='pvmodel',
            name='year_one_to_massproducer_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='steamturbinemodel',
            name='can_supply_mp',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='steamturbinemodel',
            name='year_one_electric_to_massproducer_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='steamturbinemodel',
            name='year_one_thermal_to_massproducer_series_mmbtu_per_hr',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='storagemodel',
            name='year_one_to_massproducer_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='windmodel',
            name='year_one_to_massproducer_series_kw',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, default=list, null=True, size=None),
        ),
    ]
