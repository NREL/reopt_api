# Generated by Django 2.2.13 on 2021-02-10 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0079_pvmodel_pv_ppa_cost_us_dollars'),
    ]

    operations = [
        migrations.AddField(
            model_name='storagemodel',
            name='existing_kw',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='storagemodel',
            name='existing_kwh',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
