# Generated by Django 2.2.13 on 2020-12-02 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reo', '0075_auto_20201202_0327'),
    ]

    operations = [
        migrations.AddField(
            model_name='loadprofilemodel',
            name='bau_sustained_time_steps',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]