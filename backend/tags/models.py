from django.db import models


class Tag(models.Model):
    """Хранение информации о тегах."""
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField(
        'Слаг',
        max_length=32,
        unique=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name
