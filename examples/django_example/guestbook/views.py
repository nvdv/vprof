"""Remote profiling example with Flask.
First of all launch vprof in remote mode:

    vprof -r

and launch this app:

    python manage.py runserver 127.0.0.1:8080

You can profile '/' and '/add' handlers:

    curl http://127.0.0.1:8080/guestbook/profile/

and

    curl --data "name=foo&message=bar" http://127.0.0.1:8080/guestbook/profile/add

Check profile source code below for more details.

Note that vprof -r should be relaunched after each run.
"""

from django import http
from django.template import loader
from guestbook import models
from django.views.decorators.csrf import csrf_exempt
from django.core import urlresolvers
from vprof import profiler


def show_guestbook(request):
    """Returns all existing guestbook records."""
    template = loader.get_template('index.html')
    entries = models.Entry.objects.all()
    return http.HttpResponse(template.render({'entries': entries}, request))


@csrf_exempt
def add_entry(request):
    """Adds single guestbook record."""
    if request.method == 'POST':
        models.Entry(
        name=request.POST['name'], message=request.POST['message']).save()
    return http.HttpResponseRedirect(
        urlresolvers.reverse('show_guestbook'), request)

@csrf_exempt
def profile(request, uri):
    """Profiler handler."""
    if uri == '':
        profiler.run(show_guestbook, 'cmh', args=(request,))
    elif uri == 'add':
        profiler.run(add_entry, 'cmh', args=(request,))
    return http.HttpResponseRedirect(
        urlresolvers.reverse('show_guestbook'), request)
