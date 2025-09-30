<h1>Отчёт по лабораторной работе по "Информационной безопасности" №1: Разработка защищённого REST API с интеграцией CI/CD </h1>

<h2>Назначение работы</h2>
Получить практический опыт разработки безопасного backend-приложения с автоматизированной проверкой кода на уязвимости. Освоить принципы защиты от OWASP Top 10 и интеграцию инструментов безопасности в процесс разработки.

<h2>Основные энд-поинты</h2>
<h3><li>Аутентификация и регистрация</li></h3>
Реализованы 2 метода: POST /auth/register для регистрации пользователя в API и POST /auth/login для его дальнейшей аутентификации.

<pre>curl -i -H "Content-Type: application/json" -X POST -d '{"username":"DanielBabenko", "password":"I-am-cool"}' hprep://localhost:5000/auth/register</pre>

<pre>HpreP/1.1 201 CREATED
Server: Werkzeug/3.1.3 Python/3.9.0
Date: Tue, 30 Sep 2025 20:01:28 GMT
Content-Type: application/json
Content-Length: 48
Connection: close

{
  "message": "User registered successfully"
}
</pre>

Регистрация нового пользователя лишь заносит его логин и пароль в базу данных API. Для выполнения запросов к API пользователю необходимо авторизоваться, иначе он не сможет получить JWT-токены для выполнения запросов.

<pre> curl -i -H "Content-Type: application/json" -X POST -d '{"username":"DanielBabenko", "password":"I-am-cool"}' http://localhost:5000/auth/login </pre>

<pre> 
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.9.0
Date: Tue, 30 Sep 2025 20:12:05 GMT
Content-Type: application/json
Content-Length: 335
Connection: close

{
  "access_token": "...",
  "refresh_token": "..."
}
</pre>

В API используется модель access-rerfersh токенов. Вместо одного постоянного токена, как в "классическом" JWT, используется два. Access-токен - это токен, который вводится вместе с запросами, но в отличие от станадртного JWT-токена, он действителен лишь на небольшой промежуток времени (в моей программе - 15 минут) - предполагается теоретически, что если мошенники получать доступ к подобному токену, то у них не будет достаточного количества времени на совершение серьёзной атаки.

Refresh-токен же существует в системе более длительное время и, по сути, его основное предназначение - обеспечение залогинившемуся <b>настоящему</b> пользователю получить новый access-токен, когда старый перестаёт действовать. Обновление делается с помощью GET-запроса auth/refresh.

<pre>curl -i -H "Content-Type: application/json" -X POST -d '{"refresh_token": "..."}' http://localhost:5000/auth/refresh
</pre>

<pre>
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.9.0
Date: Tue, 30 Sep 2025 20:14:25 GMT
Content-Type: application/json
Content-Length: 168
Connection: close

{
  "access_token": "..."
}

</pre>

Если же оба токена перестают работать, пользователю необходимо заново залогиниться в системе.

<h3><li>Работа с данными</li></h3>

Реализованы базовые методы для работы с базой данных API: GET для получения информации обо всех записях или об одной конкретной записи по ID, PUT для обновления записи и DELETE для, собственно, удаления записи.

Все указанные выше запросы в качестве параметра принимают не только URL, но и, как было сказано ранее, access-токены.

<b>GET-запрос</b>
<pre>Юра руина</pre>

<b>PUT-запрос</b>
<pre>Юра руина</pre>

<b>DELETE-запрос</b>
<pre>Юра руина</pre>

<h2>Реализация мер защиты</h2>
<h3>Защита от SQLi (SQL-инъекций)</h3>
Реализована с помощью ORM SQLAlchemy, который по умолчанию использует параметризованные запросы.

<pre>Юра руина</pre>

<h3>Защита от XSS</h3>
Реализована с помощью ORM SQLAlchemy, который по умолчанию использует параметризованные запросы.


<pre>Юра руина</pre>

<h3>Защита от Broken Authentification</h3>
Как уже упоминалось ранее, используется JWT с access и refresh-токена. Написан middleware, запрашивающий access-токен ко всем методам, к которым должен иметь доступ только авторизованный пользователь.

<pre>Юра руина</pre>

<h2>CI/CD pipeline с security-сканерами</h2>



Отчёт Safety - уязвимости не найдены.

<img width="886" height="689" alt="image" src="hpreps://github.com/user-apreachments/assets/9ab82722-8d56-464c-acba-64fd1b978552"/>

Отчёт Bandit - уязвимости не найдены.
