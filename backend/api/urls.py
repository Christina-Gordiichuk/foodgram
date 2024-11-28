from django.urls import include, path

from ingredients.views import IngredientDetailView, IngredientListView

from recipes.views import (
    RecipeListView,
    RecipeDetailView,
    RecipeCreateView,
    RecipeUpdateView,
    RecipeDeleteView,
    RecipeShortLinkView,
    DownloadShoppingListView,
    AddRecipeToShoppingListView,
    RemoveRecipeFromShoppingListView,
    AddRecipeToFavoritesView,
    RemoveFavoriteView,
)

from tags.views import TagDetailView, TagListView

from users.views import (
    ChangePasswordView,
    CurrentUserView,
    UpdateAvatarView,
    UserListView,
    UserProfileView,
    MySubscriptionsView,
    SubscribeView,
    UnsubscribeView,
)

urlpatterns = [
    # Получаем список пользователей.
    path(
        'users/',
        UserListView.as_view(),
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
        'users/me/password/',
        ChangePasswordView.as_view(),
        name='change-password'
    ),
    # Подписки.
    path(
        'subscriptions/',
        MySubscriptionsView.as_view(),
        name='my_subscriptions'
    ),
    # Подписаться на пользователя.
    path(
        'subscribe/<int:id>/',
        SubscribeView.as_view(),
        name='subscribe'
    ),
    # Отписаться от пользователя.
    path(
        'unsubscribe/<int:id>/',
        UnsubscribeView.as_view(),
        name='unsubscribe'
    ),
    # Получение токена.
    path(
        'auth/',
        include('djoser.urls.authtoken')
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
    # Список рецептов.
    path(
        'recipes/',
        RecipeListView.as_view(),
        name='recipe-list'
    ),
    # Создание рецепта.
    path(
        'recipes/create/',
        RecipeCreateView.as_view(),
        name='recipe-create'
    ),
    # Получаем рецепт.
    path(
        'recipes/<int:id>/',
        RecipeDetailView.as_view(),
        name='recipe-detail'
    ),
    # Обновление рецепта.
    path(
        'recipes/<int:id>/update/',
        RecipeUpdateView.as_view(),
        name='recipe-update'
    ),
    # Удаление рецепта.
    path(
        'recipes/<int:id>/delete/',
        RecipeDeleteView.as_view(),
        name='recipe-delete'
    ),
    # Короткая ссылка.
    path(
        'recipes/<int:id>/short-link/',
        RecipeShortLinkView.as_view(),
        name='recipe-short-link'
    ),
    # Скачать список покупок.
    path(
        'shopping-list/download/',
        DownloadShoppingListView.as_view(),
        name='download-shopping-list'
    ),
    # Добавить рецепт в список покупок.
    path(
        'shopping-list/add/<int:id>/',
        AddRecipeToShoppingListView.as_view(),
        name='add-recipe-to-shopping-list'
    ),
    # Удалить рецепт из списка покупок.
    path(
        'shopping-list/remove/<int:id>/',
        RemoveRecipeFromShoppingListView.as_view(),
        name='remove-recipe-from-shopping-list'
    ),
    # Добавить в избранное.
    path(
        'favorites/add/<int:id>/',
        AddRecipeToFavoritesView.as_view(),
        name='add-recipe-to-favorites'
    ),
    # Удалить из избранного.
    path(
        'favorites/remove/<int:id>/',
        RemoveFavoriteView.as_view(),
        name='remove-favorite'
    ),
]
