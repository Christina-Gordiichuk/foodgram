### Workflow
[![Main Foodgram workflow](https://github.com/Christina-GordiichukPotashevIlya/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Christina-Gordiichuk/foodgram/actions/workflows/main.yml)

# Проект Foodgram
## Описание проекта 
Foodgram - это сервис для публикации рецептов самых разнообразных блюд. Вы можете публиковать собственные рецепты, изучать рецепты других пользователей, подписываться на других пользователей, добавлять рецепты в избранное, добавлять рецепты в корзину, а перед походом в магазин скачать файлом список всех необходимых ингредиентов для покупки. 

## Как запустить проект в контейнерах
1. Клонировать репозиторий и перейти в него в командной строке
```
https://github.com/Christina-Gordiichuk/foodgram
```
```
cd foodgram
```
2. Создать .env файл в корневой директории по образцу .env.example
3. Запустить docker-compose
```
docker compose -f docker-compose.production.yml up
```
4. Применить миграции в контейнере бекэнда
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
5. Предзаполнить базу данных из csv или json файлов - последовательно выполнить команды
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py fill_ingredients_from_csv/json
```
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py fill_tags_from_csv/json
```
6. Собрать статику бекэнда
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```
7. Скопировать статику в директорию, связанную с volume
```
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
8. Скопировать файлы спецификации API в директорию, связанную с volume
```
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/docs/. /backend_static/static/redoc/
```
9. Создать суперпользователя (опционально)
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

## Как запустить проект локально (будет доступен только функционал API, без фронтенда)
1. Клонировать репозиторий и перейти в него в командной строке
```
https://github.com/Christina-Gordiichuk/foodgram
```
```
cd foodgram
```
2. Создать .env файл в корневой директории по образцу .env.example
3. Перейти в директорию бекенда
```
cd backend
```
4. Создать и активировать виртуальное окружение
```
python -m venv venv
```
```
source venv/Scripts/activate
```
5. Установить зависимости проекта
```
pip install -r requirements.txt
```
6. Выполнить миграции
```
python manage.py migrate
```
7. Предзаполнить базу данных из csv или json файлов - последовательно выполнить команды
```
python manage.py fill_ingredients_from_csv/json
```
```
python manage.py fill_tags_from_csv/json
```
8. Создать суперпользователя (опционально)
```
python manage.py createsuperuser
```
9. Запустить проект
```
python manage.py runserver
```
## Доступные эндпоинты API:
- Документация со всеми эндпоинтами будет доступна по ссылке https://<ваш домен или IP>/redoc/ после запуска проекта в контейнерах. 
___
### Стек :bulb:
Python, Django, Gunicorn, nginx, Rest API (DRF), PostgreSQL, Docker, CI/CD (GitHub Actions), React, Yandex Cloud.
___  
#### Автор проекта:    
:small_orange_diamond: [Гордийчук Кристина](https://github.com/Christina-Gordiichuk)
