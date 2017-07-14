# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='runoutput',
            name='average_annual_energy_exported',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
