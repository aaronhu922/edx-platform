# Generated by Django 2.2.16 on 2020-11-28 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0040_courseenrollmentinfo_course_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseenrollmentinfo',
            name='created',
            field=models.DateField(blank=True),
        ),
        migrations.AlterField(
            model_name='courseenrollmentinfo',
            name='ended_date',
            field=models.DateField(blank=True),
        ),
    ]
