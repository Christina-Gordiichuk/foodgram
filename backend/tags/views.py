from rest_framework import generics
from .models import Tag
from api.serializers import TagSerializer


class TagListView(generics.ListAPIView):
    """Получаем список всех тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagDetailView(generics.RetrieveAPIView):
    """Получаем информацию о конкретном теге по ID."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
