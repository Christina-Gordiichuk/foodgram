import base64
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import generics, filters, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
)
from rest_framework.generics import GenericAPIView
from django_filters.rest_framework import DjangoFilterBackend

from ingredients.models import Ingredient
from recipes.models import Recipe, ShoppingCart, Favorite
from api.serializers import IngredientSerializer, RecipeSerializer
from api.pagination import CustomPagination
from api.filters import RecipeFilter
from users.models import User, Subscription
from tags.models import Tag
from api.serializers import (
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer
)


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
            serializer = self.getserializer(page, many=True)
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


class TagListView(generics.ListAPIView):
    """Получаем список всех тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagDetailView(generics.RetrieveAPIView):
    """Получаем информацию о конкретном теге по ID."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'


class UserListView(APIView):
    """
    Получаем список пользователей с поддержкой пагинации.
    Используем сериализатор UserSerializer для форматирования данных.
    """
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserProfileView(APIView):
    """
    Получаем профиль конкретного пользователя по его ID.
    Используем ID пользователя для поиска.
    """
    def get(self, request, id):
        user = get_object_or_404(User, id=id)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class CurrentUserView(APIView):
    """Получаем профиль текущего пользователя. /me/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UpdateAvatarView(APIView):
    """
    Добавляем/обновляем аватар текущего пользователя.
    Требует авторизации.
    """

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        avatar_data = request.data.get('avatar')

        if not avatar_data:
            return Response(
                {'detail': 'Аватар не предоставлен!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f'{uuid.uuid4()}.{ext}'

            user.avatar.save(
                file_name,
                ContentFile(base64.b64decode(imgstr)),
                save=True
            )

            return Response(
                {'avatar': user.avatar.url},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар не установлен.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):
    """
    Изменяем пароль текущего пользователя.
    Требует авторизации.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {'detail': 'Текущий и новый пароли обязательны!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(current_password):
            return Response(
                {'current_password': ['Неверный текущий пароль!']},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SubscriptionsView(APIView):
    """Возвращаем пользователей, на которых подписан текущий пользователь."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        subscribed_users = Subscription.objects.filter(user=user).values_list(
            'subscribed_user', flat=True
        )
        users = (
            User.objects
            .filter(id__in=subscribed_users)
            .prefetch_related('recipes')
        )
        serializer = UserWithRecipesSerializer(users, many=True)
        return Response(serializer.data)


class SubscribeView(APIView):
    """Подписаться на пользователя."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        subscribed_user = get_object_or_404(User, id=id)
        if Subscription.objects.filter(
            user=request.user,
            subscribed_user=subscribed_user
        ).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(
            user=request.user,
            subscribed_user=subscribed_user
        )
        serializer = UserWithRecipesSerializer(subscribed_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnsubscribeView(APIView):
    """Отписаться от пользователя."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id):
        subscribed_user = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            user=request.user,
            subscribed_user=subscribed_user
        )

        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Подписка не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )
