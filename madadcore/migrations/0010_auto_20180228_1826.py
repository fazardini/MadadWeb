# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-28 18:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('madadcore', '0009_auto_20180202_1812'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='surplusdrug',
            unique_together=set([]),
        ),
    ]
