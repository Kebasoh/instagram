from django.urls import path,re_path
from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',views.index, name ='index'),
    path('profile/<int:id>/',views.profile,name='profile'),
    path('post/<int:id>/',views.post,name="post"),
    path(r'search',views.search,name='search'),
    path('like',views.like,name='like'),
    

] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)




