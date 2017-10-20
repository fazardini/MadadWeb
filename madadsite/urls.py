from django.conf.urls import url
from madadsite.views import *

urlpatterns = [
    url(r'^register/', register, name='register'),
    url(r'^login/', user_login, name='login'),
    url(r'^logout/', user_logout, name='logout'),
    url(r'^drugs/(?P<safe_id>[0-9a-f]{16})/$', hospital_drugs,  name='hospital_drugs'),
    url(r'^hospitals/$', all_hospitals,  name='all_hospitals'),
    url(r'^drugs/all/$', all_drugs,  name='all_drugs'),
    url(r'^drugs-name/', drugs_name, name='drugs_name'),
]
