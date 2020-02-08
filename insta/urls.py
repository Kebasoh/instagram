from django.conf.urls import url
from . import views


urlpatterns=[
    url('^$',views.insta,name = 'insta'),
    url('^today/$',views.insta_of_day,name='instaToday')
]