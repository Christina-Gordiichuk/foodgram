from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from ingredients.models import Ingredient
from tags.models import Tag


User = get_user_model()

COOKING_TIME_MIN = 1
COOKING_TIME_MAX = 32000

AMOUNT_MIN = 1
AMOUNT_MAX = 32000


class Recipe(models.Model):
    """Модель для хранения информации о рецептах."""
    name = models.CharField('Название', max_length=256)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    image = models.ImageField('Изображение', upload_to='recipes/')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (мин)',
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN,
                message=(
                    f'Время приготовления не меньше {COOKING_TIME_MIN} минут.'
                ),
            ),
            MaxValueValidator(
                COOKING_TIME_MAX,
                message=(
                    f'Время приготовления не больше {COOKING_TIME_MAX} минут.'
                ),
            )
        ]
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    in_shopping_cart = models.ManyToManyField(
        User,
        related_name='shopping_cart_recipes',
        through='ShoppingCart',
        blank=True,
        verbose_name='В корзине покупок'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['name']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель для указания количества ингредиентов в рецепте."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='in_recipes',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                AMOUNT_MIN,
                message=f'Количество не может быть меньше {AMOUNT_MIN}.'
            ),
            MaxValueValidator(
                AMOUNT_MAX,
                message=f'Количество не может превышать {AMOUNT_MAX}.'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ['ingredient__name']

    def __str__(self):
        return f'{self.ingredient.name} в {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель для списка покупок пользователя. """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ['user', 'recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe_in_cart'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} в списке покупок у {self.user.username}'


class Favorite(models.Model):
    """Модель для избранных рецептов пользователей."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт',
    )
    created_at = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} добавил в избранное {self.recipe.name}'
