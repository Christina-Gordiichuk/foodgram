import base64
from rest_framework import serializers
from recipes.models import Recipe
from users.models import Subscription, MyUser


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели MyUser."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        ]

    def get_avatar(self, obj):
        """Преобразуем изображение в строку Base64."""
        if obj.avatar:
            with open(obj.avatar.path, 'rb') as image_file:
                encoded_string = (
                    base64.b64encode(image_file.read())
                    .decode('utf-8')
                )
                return f'data:image/jpeg;base64,{encoded_string}'
        return None

    def get_is_subscribed(self, obj):
        """
        Определяем, подписан ли текущий пользователь на данного пользователя.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                subscribed_user=obj
            ).exists()
        return False


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для минимизированного представления рецепта."""

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя с его рецептами и информацией о подписке."""
    recipes = RecipeMinifiedSerializer(many=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta:
        model = MyUser
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        ]

    def get_is_subscribed(self, obj):
        """
        Определяем, подписан ли текущий пользователь на данного пользователя.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                subscribed_user=obj
            ).exists()
        return False
