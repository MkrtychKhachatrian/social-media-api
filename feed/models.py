import os
import uuid

from django.db import models
from django.utils.text import slugify

from social_media_api import settings


class Hashtag(models.Model):
    name = models.CharField(max_length=63, unique=True)


class Post(models.Model):
    text = models.TextField()
    hashtags = models.ManyToManyField(to=Hashtag, related_name="posts", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Post id: {self.id}"


def profile_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.username)}--{uuid.uuid4()}.{extension}"
    return os.path.join("uploads/profiles", filename)


class Profile(models.Model):
    user = models.OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    username = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(null=True, upload_to=profile_image_file_path, blank=True)
    following = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="followers"
    )

    def __str__(self):
        return self.username
