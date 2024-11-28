from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """
    Кастомный класс пагинации для работы с параметрами 'page' и 'limit'.
    Количество объектов по умолчанию на одной странице.
    Параметр для ограничения количества объектов на странице.
    Параметр для номера страницы.
    """
    page_size = 10
    page_size_query_param = 'limit'
    page_query_param = 'page'
