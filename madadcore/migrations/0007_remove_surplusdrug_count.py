# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-25 20:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('madadcore', '0006_auto_20171025_2000'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='surplusdrug',
            name='count',
        ),
    ]
