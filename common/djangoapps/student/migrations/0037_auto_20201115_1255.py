# Generated by Django 2.2.16 on 2020-11-15 12:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0036_courseenrollmentinfo'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_service_name', models.CharField(max_length=250)),
                ('customer_service_info', models.TextField(blank=True, max_length=1024)),
            ],
            options={
                'verbose_name': 'customer_service',
            },
        ),
        migrations.AddField(
            model_name='courseenrollmentinfo',
            name='customer_service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='student.CustomerService'),
        ),
    ]
