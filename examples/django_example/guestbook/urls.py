from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.show_guestbook, name='show_guestbook'),
    url(r'^add/$', views.add_entry, name='add_entry'),
    url(r'^profile/(?P<uri>\w{0,10})$', views.profile, name='profile'),
]
