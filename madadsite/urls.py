from django.conf.urls import url
from madadsite.views import *

urlpatterns = [
    url(r'^register/', register, name='register'),
    url(r'^login/', user_login, name='login'),
    url(r'^logout/', user_logout, name='logout'),

    #  daroohaye mazad in bomarestan
    url(r'^drugs/(?P<safe_id>[0-9a-f]{16})/$', my_drugs,  name='my_drugs'),

    # daroohaie ke in bimarestan sefaresh dade
    url(r'^ordered-drugs/(?P<safe_id>[0-9a-f]{16})/$', ordered_drugs,  name='ordered_drugs'),

    # daroohaie ke in bimarestan sefaresh gerefte
    url(r'^order-token-drugs/(?P<safe_id>[0-9a-f]{16})/$', order_token_drugs, name='order_token_drugs'),

    # hame daroohaye mazad
    url(r'^drugs/all/$', all_drugs, name='all_drugs'),

    # hame bimarestan ha
    url(r'^hospitals/$', all_hospitals,  name='all_hospitals'),

    # autocompelete name darooha
    url(r'^drugs-name/', drugs_name, name='drugs_name'),

    # taghire state darooye sefaresh dade shode
    url(r'^change-order-state/', change_order_state, name='change_order_state'),

    # taghire state darooye sefaresh dade shode
    url(r'^hospitals-drug/', hospitals_drug, name='hospitals_drug'),

    # taghire state darooye sefaresh dade shode
    url(r'^save-order/', save_order, name='save_order'),
]
