# Generated by Django 2.2.16 on 2020-12-27 02:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pdfexam', '0006_auto_20201226_0742'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapprofileextresults',
            name='check_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checked_items', to='pdfexam.MapTestCheckItem'),
        ),
    ]
