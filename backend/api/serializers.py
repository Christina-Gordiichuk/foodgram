import base64
import uuid

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers, validators

from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from tags.models import Tag
from users.models import User


# Ограничения поля amount.
AMOUNT_MIN = 1
AMOUNT_MAX = 32000


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
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN,
        max_value=AMOUNT_MAX,
        error_messages={
            'min_value': (
                f'Количество ингредиента не может быть меньше {AMOUNT_MIN}.'
            ),
            'max_value': (
                f'Количество ингредиента не может превышать {AMOUNT_MAX}.'
            ),
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount'
        ]
        ordering = ['id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели MyUser."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
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
            if obj.avatar and hasattr(obj.avatar, 'file'):
                encoded_string = (
                    base64.b64encode(obj.avatar.read())
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
            return obj.subscribers.filter(user=request.user).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    author = UserSerializer(read_only=True)
    ingredients = IngredientsSerializer(source='recipe_ingredients',
                                        many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    in_shopping_cart = serializers.SerializerMethodField(
        default=False,
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        min_value=AMOUNT_MIN,
        max_value=AMOUNT_MAX,
        error_messages={
            'min_value': (
                f'Время приготовления не может быть меньше {AMOUNT_MIN}.',
            ),
            'max_value': (
                f'Время приготовления не может превышать {AMOUNT_MAX}.'
            )
        }
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
            'in_shopping_cart'
        ]

    def get_is_in_shopping_cart(self, obj):
        """Проверяем, находится ли рецепт в корзине покупок у пользователя."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.in_shopping_cart.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        """Создаем новый рецепт."""
        if (
            'ingredients' not in self.initial_data
            or 'tags' not in self.initial_data
        ):
            raise serializers.ValidationError(
                'Теги и ингредиенты обязательны.'
            )
        ingredients = self.initial_data['ingredients']
        tags = self.initial_data['tags']
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(get_object_or_404(Tag, pk=id) for id in tags)
        self._process_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляем экземпляр рецепта с указанными данными."""
        if (
            'ingredients' not in self.initial_data
            or 'tags' not in self.initial_data
        ):
            raise serializers.ValidationError(
                'Теги и ингредиенты обязательны.'
            )

        ingredients = self.initial_data['ingredients']
        tags = self.initial_data['tags']
        cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if not (AMOUNT_MIN <= cooking_time <= AMOUNT_MAX):
            raise serializers.ValidationError({
                'cooking_time': (
                    f'Время приготовления должно быть между {AMOUNT_MIN} и'
                    f'{AMOUNT_MAX}.'
                )
            })
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        instance.tags.set(get_object_or_404(Tag, pk=id) for id in tags)
        instance.recipe_ingredients.all().delete()

        self._process_ingredients(instance, ingredients)
        return instance

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
        model = User
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
            return obj.subscribers.filter(user=request.user).exists()
        return False
