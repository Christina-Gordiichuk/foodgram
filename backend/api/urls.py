from django.urls import include, path

from api.views import (
    AddRecipeToShoppingListView,
    ChangePasswordView,
    CurrentUserView,
    DownloadShoppingListView,
    IngredientDetailView,
    IngredientListView,
    RecipeAPIView,
    RecipeDetailView,
    RecipeShortLinkView,
    RecipeFavoritesView,
    SubscriptionsView,
    SubscribeView,
    TagDetailView,
    TagListView,
    UpdateAvatarView,
    UsersView,
    UserProfileView,
)


urlpatterns = [
    # Получение токена.
    path(
        'auth/',
        include('djoser.urls.authtoken')
    ),
    path(
        'auth/users/', 
        include('djoser.urls')
    ),
    # Получаем список пользователей.
    path(
        'users/',
        UsersView.as_view(),
        name='user-list'
    ),
    # Профиль пользователя по ID.
    path(
        'users/<int:id>/',
        UserProfileView.as_view(),
        name='user-profile'
    ),
    # Профиль текущего пользователя.
    path(
        'users/me/',
        CurrentUserView.as_view(),
        name='current-user'
    ),
    # Обновление аватара.
    path(
        'users/me/avatar/',
        UpdateAvatarView.as_view(),
        name='update-avatar'
    ),
    # Изменение пароля.
    path(
        'users/set_password/',
        ChangePasswordView.as_view(),
        name='change-password'
    ),
    # Подписки.
    path(
        'users/subscriptions/',
        SubscriptionsView.as_view(),
        name='my_subscriptions'
    ),
    # Подписаться на пользователя. Отписаться от пользователя.
    path(
        'users/<int:id>/subscribe/',
        SubscribeView.as_view(),
        name='subscribe'
    ),
    # Список тегов.
    path(
        'tags/',
        TagListView.as_view(),
        name='tag-list'
    ),
    # Получение тега по ID.
    path(
        'tags/<int:id>/',
        TagDetailView.as_view(),
        name='tag-detail'
    ),
    # Список ингредиентов.
    path(
        'ingredients/',
        IngredientListView.as_view(),
        name='ingredient-list'
    ),
    # Получение ингредиента по ID.
    path(
        'ingredients/<int:id>/',
        IngredientDetailView.as_view(),
        name='ingredient-detail'
    ),
    # Создаем, получаем, обновляем, удаляем рецепт.
    path(
        'recipes/',
        RecipeAPIView.as_view(),
        name='recipe-list'
    ),
    # Получаем рецепт.
    path(
        'recipes/<int:id>/',
        RecipeDetailView.as_view(),
        name='recipe-detail'
    ),
    # Короткая ссылка.
    path(
        'recipes/<int:id>/get-link/',
        RecipeShortLinkView.as_view(),
        name='recipe-short-link'
    ),
    # Скачать список покупок.
    path(
        'recipes/download_shopping_cart/',
        DownloadShoppingListView.as_view(),
        name='download-shopping-list'
    ),
    # Добавить рецепт в список покупок. Удалить рецепт из списка покупок.
    path(
        'recipes/<int:id>/shopping_cart/',
        AddRecipeToShoppingListView.as_view(),
        name='add-recipe-to-shopping-list'
    ),
    # Добавить в избранное. Удалить из избранного.
    path(
        'recipes/<int:id>/favorite/',
        RecipeFavoritesView.as_view(),
        name='add-recipe-to-favorites'
    )
]