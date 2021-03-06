# Generated by Django 2.2.16 on 2020-11-15 10:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0035_bulkchangeenrollmentconfiguration'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEnrollmentInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_user_name', models.CharField(max_length=250)),
                ('course_user_password', models.CharField(max_length=255)),
                ('course_school_code', models.CharField(blank=True, max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('ended_date', models.DateTimeField(auto_now=True)),
                ('description', models.TextField(blank=True, max_length=1024)),
                ('course_enrolled', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.CourseEnrollment')),
            ],
            options={
                'verbose_name_plural': 'courses-students-list',
                'verbose_name': 'courses-students',
            },
        ),
    ]
