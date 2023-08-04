from django.urls import path, include
from rest_framework import routers

from feed.views import (
    PostViewSet,
    HashtagViewSet,
    ProfileViewSet,
)


router = routers.DefaultRouter()
router.register("posts", PostViewSet)
router.register("tags", HashtagViewSet)
router.register("profiles", ProfileViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "feed"
