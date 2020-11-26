from django.conf.urls import url
from . import views
urlpatterns = [
 #   url(r'^$', views.choose_file),
    url(r'^upload', views.upload_file),
    url(r'^handle', views.Handle),
 #   url(r'^(\d+)$', views.show)
]
