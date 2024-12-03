from rest_framework import generics
from .models import Ingredient
from api.serializers import IngredientSerializer


class IngredientListView(generics.ListAPIView):
    """
    Получаем список ингредиентов с возможностью поиска по имени.
    """
    serializer_class = IngredientSerializer

    def get_queryset(self):
        name = self.request.query_params.get('name', None)
        queryset = Ingredient.objects.all()
        if name:
            queryset = queryset.filter(name__startswith=name)
        return queryset


class IngredientDetailView(generics.RetrieveAPIView):
    """Получаем ингредиент по его ID."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    lookup_field = 'id'
