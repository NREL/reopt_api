# Generated by Django 2.2.13 on 2021-01-08 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0098_auto_20201231_1804'),
    ]

    operations = [
        migrations.AddField(
            model_name='flextechwhmodel',
            name='max_kw',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='flextechwhmodel',
            name='min_kw',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
