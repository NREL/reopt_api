# Generated by Django 2.2.6 on 2019-10-30 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0049_auto_20191030_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilemodel',
            name='parse_run_outputs_seconds2',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profilemodel',
            name='pre_setup_scenario_seconds2',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profilemodel',
            name='reopt_bau_seconds2',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profilemodel',
            name='reopt_seconds2',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profilemodel',
            name='setup_scenario_seconds2',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
