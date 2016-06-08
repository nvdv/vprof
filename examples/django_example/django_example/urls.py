"""django_example URL Configuration."""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^guestbook/', include('guestbook.urls')),
]
