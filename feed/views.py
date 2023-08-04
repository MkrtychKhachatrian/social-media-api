from datetime import datetime

from django.db.models import Q, Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from feed.models import Post, Profile, Hashtag
from feed.pagination import PostsPagination
from feed.permissions import IsOwnerOrReadOnly
from feed.serializers import (
    PostSerializer,
    ProfileSerializer,
    PostListSerializer,
    HashtagSerializer,
    ProfileListSerializer,
    ProfileDetailSerializer,
    ProfileImageSerializer,
    PostDetailSerializer,
)


class HashtagViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer
    permission_classes = (IsAuthenticated,)


class PostViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Post.objects.prefetch_related("hashtags").select_related(
        "user", "user__profile"
    )
    serializer_class = PostSerializer
    pagination_class = PostsPagination
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Show only users' posts or posts of people user is following"""
        queryset = self.queryset
        following = self.request.user.profile.following.values("user")
        queryset = queryset.filter(Q(user=self.request.user) | Q(user__in=following))
        """Retrieve the posts with filters"""
        hashtag = self.request.query_params.get("hashtag")
        date = self.request.query_params.get("date")

        if hashtag:
            queryset = queryset.filter(hashtags__name__icontains=hashtag)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(created_at__date=date)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostSerializer

    @action(detail=False, methods=["get"])
    def my_posts(self, request):
        """Get all posts for the authenticated user"""
        posts = Post.objects.filter(user=request.user)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "hashtag",
                type=OpenApiTypes.INT,
                description="Filter posts by hashtag (ex. ?hashtag=happy)",
            ),
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description=(
                    "Filter by datetime of posts creation " "(ex. ?date=2022-10-23)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ProfileViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Profile.objects.prefetch_related("following").select_related("user")
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def create(self, request, *args, **kwargs):
        """Raise error when user already has a profile"""
        if request.user.profile:
            raise serializers.ValidationError("You have already created a profile.")

        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileListSerializer
        elif self.action == "retrieve":
            return ProfileDetailSerializer
        elif self.action == "upload_photo":
            return ProfileImageSerializer
        return ProfileSerializer

    def get_queryset(self):
        """Retrieve the profiles with filters"""
        queryset = self.queryset
        username = self.request.query_params.get("username")
        city = self.request.query_params.get("city")
        if self.action == "list":
            queryset = queryset.annotate(followers_count=Count("followers"))
        if username:
            queryset = queryset.filter(username__icontains=username)
        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "username",
                type=OpenApiTypes.INT,
                description="Filter profiles by username (ex. ?username=bob_123)",
            ),
            OpenApiParameter(
                "city",
                type=OpenApiTypes.DATE,
                description="Filter profiles by city" "(ex. ?city=Kyiv)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """User profile"""
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def following(self, request):
        """Show profiles the user follows"""
        profile = self.get_object()
        if profile == request.user.profile:
            following = profile.following.all()
            serializer = self.get_serializer(following, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["get"])
    def followers(self, request):
        """Profiles of users who follows authenticated user"""
        profile = self.get_object()
        followers = Profile.objects.filter(following__in=[profile])
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def follow(self, request):
        """Follow the profile you're looking at"""
        profile = self.get_object()
        following_profile = request.user.profile
        following_profile.following.add(profile)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], permission_classes=[IsAuthenticated])
    def unfollow(self, request):
        """Unfollow the profile you're looking at"""
        profile = self.get_object()
        following_profile = request.user.profile
        following_profile.following.remove(profile)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-photo",
    )
    def upload_photo(self, request):
        """Endpoint for uploading photo to profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
