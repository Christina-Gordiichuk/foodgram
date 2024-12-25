from django_filters import rest_framework as filters
from django.db.models import Exists, OuterRef, Q
from recipes.models import Recipe, Favorite, ShoppingCart
from tags.models import Tag

class RecipeFilter(filters.FilterSet):
    """
    Filter for the Recipe model.
    Filters recipes by:
    - Favorites (is_favorited)
    - Shopping cart (is_in_shopping_cart)
    - Author (author)
    - Tags (tags)
    """
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        """
        Filter recipes based on whether they are in the user's favorites.
        """
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(Exists(Favorite.objects.filter(user=user, recipe=OuterRef('pk'))))
        elif user.is_authenticated and not value:
            return queryset.exclude(Exists(Favorite.objects.filter(user=user, recipe=OuterRef('pk'))))
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Filter recipes based on whether they are in the user's shopping cart.
        """
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(Exists(ShoppingCart.objects.filter(user=user, recipe=OuterRef('pk'))))
        elif user.is_authenticated and not value:
            return queryset.exclude(Exists(ShoppingCart.objects.filter(user=user, recipe=OuterRef('pk'))))
        return queryset
