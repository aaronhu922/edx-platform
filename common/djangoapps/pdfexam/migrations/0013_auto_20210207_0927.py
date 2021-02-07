# Generated by Django 2.2.16 on 2021-02-07 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdfexam', '0012_auto_20210203_0145'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapstudentprofile',
            name='achievement_above_mean',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AddField(
            model_name='mapstudentprofile',
            name='flesch_kincaid_grade_level',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='mapstudentprofile',
            name='growth_goals_date',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='mapstudentprofile',
            name='lexile_score',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='mapstudentprofile',
            name='relative_strength_list',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='mapstudentprofile',
            name='suggested_area_of_focus_list',
            field=models.CharField(default='', max_length=20),
        ),
    ]
