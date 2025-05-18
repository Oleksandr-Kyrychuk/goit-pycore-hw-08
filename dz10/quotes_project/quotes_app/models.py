from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Author(models.Model):
    fullname = models.CharField(max_length=100, unique=True)
    born_date = models.CharField(max_length=100, blank=True)
    born_location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.fullname

class Quote(models.Model):
    quote = models.TextField(unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.quote

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    quotes = models.ManyToManyField(Quote)

    def __str__(self):
        return self.name