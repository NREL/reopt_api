# Generated by Django 2.2.13 on 2020-10-22 17:14

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0081_flextechacmodel_flextechhpmodel_rcmodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='flextechacmodel',
            name='size_kw',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flextechhpmodel',
            name='size_kw',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rcmodel',
            name='shr',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, null=True, size=None),
        ),
    ]
