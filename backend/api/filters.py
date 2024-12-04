import django_filters
from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для модели Recipe.
    Фильтруем рецепты по избранному,
    списку покупок, автору и тегам.
    """
    is_favorited = django_filters.BooleanFilter(field_name='favorited_by__user', method='filter_is_favorited')
    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтруем рецепты по тому, добавлены ли они в избранное.
        """
        if value:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset
