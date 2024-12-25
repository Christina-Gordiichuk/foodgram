import base64
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.views import View
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from djoser.views import UserViewSet as djoser_UserViewSet

from rest_framework import generics, filters, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
)
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from ingredients.models import Ingredient
from recipes.models import Recipe, ShoppingCart, Favorite
from tags.models import Tag
from users.models import User, Subscription
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
    ShoppingCartSerializer,
    FavoriteSerializer,
)
from api.pagination import CustomPagination
from api.filters import RecipeFilter


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


class RecipeAPIView(APIView):
    """
    Unified API view for Recipe operations: list, create, update, and delete.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.all()

    def get(self, request, *args, **kwargs):
        """List recipes."""
        queryset = self.filter_queryset(self.get_queryset())
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = RecipeSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        serializer = RecipeSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Create a new recipe."""
        self.permission_classes = [permissions.IsAuthenticated]
        serializer = RecipeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, id, *args, **kwargs):
        """Update a recipe (author only)."""
        recipe = get_object_or_404(Recipe, id=id)
        self.check_object_permissions(request, recipe)
        serializer = RecipeSerializer(recipe, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, id, *args, **kwargs):
        """Delete a recipe (author only)."""
        recipe = get_object_or_404(Recipe, id=id)
        self.check_object_permissions(request, recipe)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def filter_queryset(self, queryset):
        """Apply filters to the queryset."""
        for backend in self.filter_backends:
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def check_object_permissions(self, request, obj):
        """Check permissions for object-level operations."""
        for permission in self.permission_classes:
            if not permission().has_object_permission(request, self, obj):
                self.permission_denied(request)


class RecipeDetailView(RetrieveModelMixin, APIView):
    """Получаем детальную информацию о рецепте по ID."""
    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeSerializer

    def get(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        serializer = self.serializer_class(recipe)
        return Response(serializer.data)


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
    permission_classes = [IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        data = {
            'user': request.user.id,
            'recipe': recipe.id,
        }
        serializer = ShoppingCartSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id, *args, **kwargs):
        shopping_list_item = get_object_or_404(
            ShoppingCart, user=request.user, recipe__id=id
        )
        shopping_list_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeFavoritesView(APIView):
    """Добавляем рецепт в избранное."""
    permission_classes = [IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if not created:
            return Response(
                {'detail': 'Рецепт уже в избранном!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = FavoriteSerializer(favorite)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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


class UsersView(View):
    def get(self, request, *args, **kwargs):
        view = UserListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Call Djoser's UserViewSet directly for user creation
        view = djoser_UserViewSet.as_view({'post': 'create'})
        return view(request, *args, **kwargs)


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

        if request.user.subscriptions.filter(
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

    def delete(self, request, id):
        subscribed_user = get_object_or_404(User, id=id)
        subscription = request.user.subscriptions.filter(
            subscribed_user=subscribed_user
        )

        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Подписка не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )
