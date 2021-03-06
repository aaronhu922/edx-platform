from rest_framework import serializers
from student.models import CourseEnrollmentInfo, CustomerService, UserProfile, CourseEnrollment
from django.contrib.auth.models import User
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, CourseOverviewExtendInfo


class CourseEnrollmentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollmentInfo
        fields = (
            'id', 'course_enrolled', 'course_id', 'course_user_name', 'course_user_password', 'course_school_code',
            'created',
            'ended_date', 'description', 'customer_service')


class CustomerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerService
        fields = ('id', 'customer_service_name', 'customer_service_info')


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'password', 'username',)


class StudentSerializer(serializers.ModelSerializer):
    user = AccountSerializer(required=True)
    courses_count = serializers.SerializerMethodField('enrolled_courses_count')

    def enrolled_courses_count(self, user):
        return CourseEnrollment.objects.filter(user=user.user, is_active=1).count()

    class Meta:
        model = UserProfile
        fields = ('user', 'phone_number', "web_accelerator_name", "web_accelerator_link", "courses_count")


class CourseOverviewExtendInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for a course run overview extended info.
    """

    class Meta(object):
        model = CourseOverviewExtendInfo
        fields = ('course_outside', 'course_link', 'course_grade', 'course_price', 'course_recommend_level', 'course_highlight')


class CourseOverviewSerializer(serializers.ModelSerializer):
    """
    Serializer for a course run overview.
    """
    course_ext_info = CourseOverviewExtendInfoSerializer(required=False)

    class Meta(object):
        model = CourseOverview
        fields = ('id', 'org', 'display_name', 'course_ext_info')

    # def to_representation(self, instance):
    #     representation = super(CourseOverviewSerializer, self).to_representation(instance)
    #     representation['display_name_with_default'] = instance.display_name_with_default
    #     representation['has_started'] = instance.has_started()
    #     representation['has_ended'] = instance.has_ended()
    #     representation['pacing'] = instance.pacing
    #     return representation


