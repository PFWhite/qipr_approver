# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-09 16:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('approver', '0006_auto_20170209_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='person', to='approver.ClinicalDepartment'),
        ),
    ]