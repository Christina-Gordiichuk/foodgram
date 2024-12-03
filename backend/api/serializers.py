import base64
import uuid

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from rest_framework import serializers, validators

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from tags.models import Tag
from users.models import MyUser, Subscription


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""
    ingredient = IngredientSerializer()

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'amount']


class Base64ImageField(serializers.Field):
    """
    Сериализатор для обработки изображений в формате base64.
    Преобразуем строку в формате base64 в файл и обратно.
    """
    def to_internal_value(self, data):
        try:
            format, datastr = data.split(';base64,')
            ext = format.split('/')[-1]
            file = ContentFile(base64.b64decode(datastr),
                               name=str(uuid.uuid4()) + '.' + ext)
        except Exception:
            raise serializers.ValidationError('Ошибка кодирования base64.')
        return file

    def to_representation(self, value):
        if not value:
            return None
        return value.url


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    author = UserSerializer(read_only=True)
    ingredients = IngredientsSerializer(source='recipe_ingredients',
                                        many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        default=False,
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'ingredients',
            'tags',
            'is_favorited',
            'name',
            'text',
            'cooking_time',
            'image',
            'is_in_shopping_cart'
        ]

    def get_is_in_shopping_cart(self, obj):
        """Проверяем, находится ли рецепт в корзине покупок у пользователя."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (
                ShoppingCart.objects
                .filter(user=request.user, recipe=obj)
                .exists()
            )
        return False

    def create(self, validated_data):
        """Создаем новый рецепт."""
        try:
            ingredients = self.initial_data['ingredients']
            tags = self.initial_data['tags']
        except KeyError:
            raise validators.ValidationError()
        recipe = Recipe.objects.create(**validated_data)
        for id in tags:
            tag = get_object_or_404(Tag, pk=id)
            recipe.tags.add(tag)
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           pk=item['id'])
            RecipeIngredient.objects.create(recipe=recipe,
                                            ingredient=ingredient,
                                            amount=item['amount'])
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        """Обновляем экземпляр рецепта с указанными данными."""
        try:
            ingredients = self.initial_data['ingredients']
            tags = self.initial_data['tags']
        except KeyError:
            raise validators.ValidationError()
        recipe = instance
        recipe.name = validated_data.get('name', recipe.name)
        recipe.text = validated_data.get('text', recipe.text)
        recipe.cooking_time = validated_data.get('cooking_time',
                                                 recipe.cooking_time)
        recipe.image = validated_data.get('image', recipe.image)
        recipe.tags.clear()
        for id in tags:
            tag = get_object_or_404(Tag, pk=id)
            recipe.tags.add(tag)
        recipe.save()
        recipe.ingredients.clear()
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           pk=item['id'])
            RecipeIngredient.objects.create(recipe=recipe,
                                            ingredient=ingredient,
                                            amount=item['amount'])
        recipe.save()
        return recipe

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingList."""
    class Meta:
        model = ShoppingCart
        fields = ['id', 'user', 'recipe']


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    class Meta:
        model = ShoppingCart
        fields = ['id', 'user', 'recipe']


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Favorite.
    Добавляем рецепты в избранное и получаем информацию об избранном рецепте.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ['id', 'name', 'image', 'cooking_time']


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
