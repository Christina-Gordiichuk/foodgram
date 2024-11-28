from django.conf import settings
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
)

from recipes.models import Recipe, ShoppingCart, Favorite
from recipes.pagination import CustomPagination
from recipes.filters import RecipeFilter
from recipes.serializers import RecipeSerializer
from rest_framework.generics import GenericAPIView


class RecipeListView(GenericAPIView, ListModelMixin):
    """Получаем список рецептов."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipeDetailView(RetrieveModelMixin, APIView):
    """Получаем детальную информацию о рецепте по ID."""
    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeSerializer

    def get(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        serializer = self.serializer_class(recipe)
        return Response(serializer.data)


class RecipeCreateView(CreateModelMixin, APIView):
    """Создаем новый рецепт."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecipeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeUpdateView(APIView):
    """Обновляем рецепт, доступен только автору рецепта."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        if recipe.author != request.user:
            raise PermissionDenied('Вы не являетесь автором этого рецепта!')
        serializer = RecipeSerializer(recipe, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RecipeDeleteView(DestroyModelMixin, APIView):
    """Удаляем рецепт, доступно только автору."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        if recipe.author != request.user:
            raise PermissionDenied('Вы не являетесь автором этого рецепта!')
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeShortLinkView(APIView):
    """Получаем сокращенную ссылку на рецепт по его ID."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        short_link = f'{settings.SITE_URL}/r/{recipe.id}'
        return Response({'short-link': short_link})


class DownloadShoppingListView(APIView):
    """Скачиваем файл со списком покупок."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        shopping_list = ShoppingCart.objects.filter(user=request.user)
        file_content = "\n".join([str(item) for item in shopping_list])
        response = Response(file_content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class AddRecipeToShoppingListView(APIView):
    """Добавляем рецепт в список покупок."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        shopping_list_item, created = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if created:
            recipe_data = {
                'id': recipe.id,
                'name': recipe.name,
                'image': request.build_absolute_uri(recipe.image.url),
                'cooking_time': recipe.cooking_time,
            }
            return Response(recipe_data, status=status.HTTP_201_CREATED)
        return Response(
            {'detail': 'Рецепт уже в списке покупок!'},
            status=status.HTTP_400_BAD_REQUEST
        )


class RemoveRecipeFromShoppingListView(DestroyModelMixin, APIView):
    """Удаляем рецепт из списка покупок."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id, *args, **kwargs):
        shopping_list_item = get_object_or_404(
            ShoppingCart, user=request.user, recipe__id=id
        )
        shopping_list_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddRecipeToFavoritesView(CreateModelMixin, APIView):
    """Добавляем рецепт в избранное."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже в избранном!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe_data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': request.build_absolute_uri(recipe.image.url),
            'cooking_time': recipe.cooking_time,
        }
        return Response(recipe_data, status=status.HTTP_201_CREATED)


class RemoveFavoriteView(DestroyModelMixin, APIView):
    """Удаляем рецепт из избранного."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id, *args, **kwargs):
        favorite = get_object_or_404(Favorite, user=request.user, recipe_id=id)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
