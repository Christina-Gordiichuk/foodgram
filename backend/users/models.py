from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        'email',
        max_length=254,
        unique=True
    )
    username = models.CharField(
        'Логин пользователя',
        max_length=150,
        unique=True,
        validators=[RegexValidator(r'^[\w.@+-]+\Z')]
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для хранения подписок пользователей."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь'
    )
    subscribed_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписанный пользователь',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_user'],
                name='unique_user_subscription'
            )
        ]
        ordering = ['user', 'subscribed_user']

    def __str__(self):
        return (
            f'{self.user.username} подписан на '
            f'{self.subscribed_user.username}'
        )
