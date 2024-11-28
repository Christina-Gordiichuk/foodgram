from django.contrib import admin
from .models import Recipe, RecipeIngredient, ShoppingCart, Favorite


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Рецепты."""
    list_display = ('name', 'author', 'cooking_time')
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'author')
    ordering = ('-id',)
    inlines = RecipeIngredientInline,
    filter_horizontal = ('tags', 'ingredients')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Ингредиенты рецепта."""
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Список покупок."""
    list_display = ('user', 'recipe')
    list_filter = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Избранные рецепты."""
    list_display = ('user', 'recipe', 'created_at')
    list_filter = ('user', 'created_at')
