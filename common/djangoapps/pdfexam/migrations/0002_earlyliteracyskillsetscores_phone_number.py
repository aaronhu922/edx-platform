# Generated by Django 2.2.16 on 2020-12-01 07:53

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdfexam', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='earlyliteracyskillsetscores',
            name='phone_number',
            field=models.CharField(default=19951819122, max_length=50, validators=[django.core.validators.RegexValidator(message='Phone number can only contain numbers.', regex='^\\+?1?\\d*$')]),
            preserve_default=False,
        ),
    ]
