from rest_framework import serializers
from student.models import CourseEnrollmentInfo, CustomerService, UserProfile


class CourseEnrollmentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollmentInfo
        fields = ('id', 'course_enrolled', 'course_user_name', 'course_user_password', 'course_school_code', 'created',
                  'ended_date', 'description', 'customer_service')


class CustomerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerService
        fields = ('id', 'customer_service_name', 'customer_service_info')


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'name', 'phone_number', "web_accelerator_name", "web_accelerator_link")


class CourseOverViewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollmentInfo
        fields = ('id', 'course_enrolled', 'course_user_name', 'course_user_password', 'course_school_code', 'created',
                  'ended_date', 'description', 'customer_service')
