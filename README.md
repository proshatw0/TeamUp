Коротко про файлы:

app.py - главный файл - запускает веб-приложение
config.py - файл конфигурации - читает env, прописывает пути где что будет хранится
.env - скрытый файл - в них принято хранить чувствительную информацию

/app - главная папка приложения
routes.py - все наши url что мы обрабатываем
models.py - наши модели для бд
file_utils.py - необходим чтобы загружать фотографии для профиля
__init__.py - инструкции при инициализации (запуске) программы, оттуда по всему проекту app и идёт

/app/templates - тут хранятся html шаблоны страниц
type_user.html - страница для определения - пользователь/владелец
project.html - страница проекта
profile.html - страница профиля
notifications.html - страница где у нас рабоат с инвайтами
login.html - страница входа/регистрации
general.html - главная страница где поиск и так далее
favourite.html - страница избранное
employee.html - страница участника для просмотра любым пользователем
edit_project.html - страница редактирования проекта
edit_profile.html - страница редактирования профиля


/app/templates/partials - тут лежат шаблоны html кода - нужды для поиска, чтобы из данных,
        что возвращает сервер, восстановить html струтуру с новыми данными
employees_cards.html - шаблон для пользователя
project_cards.html - шаблон для проекта

/app/static - тут лежат статичные файлы такие как фото стили и js-код (у нас там пусто)

/app/static/image - тут лежат фотки

/app/static/script - тут должен лежать js, но у нас он где нужно снизу html разметки в обёртке <script><script>

/app/static/style - тут лежат стили, подписаны также как и html файлы


Коротко про развертку:

Клонировать репозиторий got clone https://github.com/proshatw0/TeamUp.git

перейти в папку, иницализировать venv:
python -m venv venv

активировать виртуально окружение:
source venv/bin/activate

установить все зависимости:
pip install -r requirements.txt

после необходимо создать БД с названием:
teamup_bd

и создать пользователя с именем паролем:
teamup_user     Super_password123321

далее за postgres выполнить:
GRANT ALL PRIVILEGES ON DATABASE teamup_bd TO teamup_user;

перейти в базу данных teamup_bd и выполнить:
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO teamup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO teamup_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO teamup_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO teamup_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO teamup_user;


теперь вернутся в папку с файлом app.py и выполнить:
flask db init
flask db migrate -m "initial migration"
flask db upgrade

Готово, теперь можно запускать:
flask run