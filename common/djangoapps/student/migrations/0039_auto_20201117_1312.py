# Generated by Django 2.2.16 on 2020-11-17 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0038_auto_20201115_1342'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='web_accelerator_link',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='web_accelerator_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
