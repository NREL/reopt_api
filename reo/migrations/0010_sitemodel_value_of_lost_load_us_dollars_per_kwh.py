# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0009_generatormodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemodel',
            name='value_of_lost_load_us_dollars_per_kwh',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
