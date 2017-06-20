# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-19 19:21
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0029_merge_20170619_1921'),
    ]

    operations = [
        migrations.AddField(
            model_name='runoutput',
            name='r_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='runoutput',
            name='r_list',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(blank=True, null=True), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='runoutput',
            name='r_max',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='runoutput',
            name='r_min',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
