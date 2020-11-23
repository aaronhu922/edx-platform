"""
URLs for student app
"""


from django.conf import settings
from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^email_confirm/(?P<key>[^/]*)$', views.confirm_email_change, name='confirm_email_change'),

    url(r'^activate/(?P<key>[^/]*)$', views.activate_account, name="activate"),

    url(r'^accounts/disable_account_ajax$', views.disable_account_ajax, name="disable_account_ajax"),
    url(r'^accounts/manage_user_standing', views.manage_user_standing, name='manage_user_standing'),

    url(r'^change_email_settings$', views.change_email_settings, name='change_email_settings'),

    url(r'^course_run/{}/refund_status$'.format(settings.COURSE_ID_PATTERN),
        views.course_run_refund_status,
        name="course_run_refund_status"),

    url(
        r'^activate_secondary_email/(?P<key>[^/]*)$',
        views.activate_secondary_email,
        name='activate_secondary_email'
    ),

    url(r'^api/manage/courseenrollments$', views.course_enrollment_info, name='course_enrollment_info'),
    url(r'^api/manage/customerservices$', views.customer_service_info, name='customer_service_info'),
    url(r'^api/manage/students$', views.students_management, name='students_management'),
    url(r'^api/manage/courses$', views.course_overview_info, name='course_overview_info'),
    url(r'^api/manage/students/(?P<pk>[0-9]+)$', views.students_management, name='students_management'),
    url(r'^api/manage/courseenrollments/(?P<id>[0-9]+)$', views.course_enrollment_info, name='course_enrollment_info'),
    url(r'^api/manage/courseenrollments/(?P<stu_id>[0-9]+)/(?P<id>[0-9]+)$', views.course_enrollment_info, name='delete_course_enrollment_info'),

]
