from django.contrib import admin
from .models import MyUser, Subscription


@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    """MyUser."""
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active', 'avatar'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)
    readonly_fields = ('date_joined', 'last_login')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Подписки пользователя."""
    list_display = ('user', 'subscribed_user')
    list_filter = ('user',)
    search_fields = ('user__username', 'subscribed_user__username')

    def __str__(self):
        return (
            f'{self.user.username} подписан на '
            f'{self.subscribed_user.username}'
        )
