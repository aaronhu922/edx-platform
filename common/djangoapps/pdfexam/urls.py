from django.conf.urls import url
from . import views
urlpatterns = [
 #   url(r'^$', views.choose_file),
    url(r'^upload', views.upload_file),
    url(r'^handle', views.Handle),
 #   url(r'^(\d+)$', views.show)
    url(r'^scaledscores/(?P<phone>[0-9]+)$', views.get_student_exam_stats, name='get_student_exam_stats'),
    url(r'^ccssitem$', views.ccss_items_management, name='ccss_items_management'),
]
