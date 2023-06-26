from rest_framework import serializers

from feed.models import Post, Hashtag, Profile


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = (
            "id",
            "word",
        )


class TagListSerializer(TagSerializer):
    class Meta:
        model = Hashtag
        fields = (
            "id",
            "word",
        )


class TagDetailSerializer(TagSerializer):
    class Meta:
        model = Hashtag
        fields = (
            "id",
            "word",
            "posts",
        )


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "user", "text", "created_at", "tags"]
        read_only_fields = ["id", "created_at"]


class PostListSerializer(PostSerializer):
    user = serializers.CharField(source="user.profile.username", read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "text_preview",
            "created_at",
            "user",
        )


class PostDetailSerializer(PostSerializer):
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="word")
    user = serializers.CharField(source="user.profile.username", read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "text",
            "tags",
            "created_at",
            "user",
        )


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "email",
            "birth_date",
            "first_name",
            "last_name",
            "city",
        )


class ProfileListSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField()

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "city",
            "followers_count",
        )


class ProfileDetailSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="user.email", read_only=True)
    posts = serializers.SerializerMethodField()
    followers = ProfileSerializer(many=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "birth_date",
            "city",
            "posts",
            "followers",
        )

    def get_posts(self, obj):
        posts = obj.user.posts.all()
        serializer = PostListSerializer(posts, many=True, context=self.context)
        return serializer.data


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "photo")
