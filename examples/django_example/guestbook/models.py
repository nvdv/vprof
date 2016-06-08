from django.db import models


class Entry(models.Model):
    """Guestbook entry."""
    name = models.CharField(max_length=20)
    message = models.TextField()
