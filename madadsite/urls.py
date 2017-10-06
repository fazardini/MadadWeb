from django.conf.urls import url
from madadsite.views import *

urlpatterns = [
    url(r'^register/', register, name='register'),
    url(r'^login/', user_login, name='login'),
    url(r'^logout/', user_logout, name='logout'),
    url(r'^drugs/(?P<safe_id>[0-9a-f]{16})/$', hospital_drugs,  name='hospital_drugs'),
]
