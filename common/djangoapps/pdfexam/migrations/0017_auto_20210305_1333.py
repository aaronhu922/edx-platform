# Generated by Django 2.2.16 on 2021-03-05 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdfexam', '0016_starreadingtestinfo_starreadingtestinforeport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='starreadingtestinfo',
            name='grade_equivalent',
            field=models.CharField(default='', max_length=10),
        ),
    ]
