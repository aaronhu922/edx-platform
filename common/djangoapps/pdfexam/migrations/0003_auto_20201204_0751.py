# Generated by Django 2.2.16 on 2020-12-04 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdfexam', '0002_earlyliteracyskillsetscores_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='earlyliteracyskillsetscores',
            name='AlphabeticPrinciple',
            field=models.IntegerField(),
        ),
    ]
