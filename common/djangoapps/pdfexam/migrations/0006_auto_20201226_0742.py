# Generated by Django 2.2.16 on 2020-12-26 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdfexam', '0005_mapprofileextresults_mapstudentprofile_maptestcheckitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapstudentprofile',
            name='MapID',
            field=models.CharField(default=5, max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='mapstudentprofile',
            name='phone_number',
            field=models.CharField(max_length=50),
        ),
    ]
