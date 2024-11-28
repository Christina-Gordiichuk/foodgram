import base64
import uuid

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MyUser, Subscription
from .serializers import UserSerializer, UserWithRecipesSerializer


class UserListView(APIView):
    """
    Получаем список пользователей с поддержкой пагинации.
    Используем сериализатор UserSerializer для форматирования данных.
    """
    def get(self, request):
        users = MyUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserProfileView(APIView):
    """
    Получаем профиль конкретного пользователя по его ID.
    Используем ID пользователя для поиска.
    """
    def get(self, request, id):
        user = get_object_or_404(MyUser, id=id)
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


class MySubscriptionsView(APIView):
    """Возвращаем пользователей, на которых подписан текущий пользователь."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        subscribed_users = Subscription.objects.filter(user=user).values_list(
            'subscribed_user', flat=True
        )
        users = (
            MyUser.objects
            .filter(id__in=subscribed_users)
            .prefetch_related('recipes')
        )
        serializer = UserWithRecipesSerializer(users, many=True)
        return Response(serializer.data)


class SubscribeView(APIView):
    """Подписаться на пользователя."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        subscribed_user = get_object_or_404(MyUser, id=id)
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
        subscribed_user = get_object_or_404(MyUser, id=id)
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
