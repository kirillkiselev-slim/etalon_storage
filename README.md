# Etalon warehouse Task

## Описание

Проект **Etalon warehouse** представляет собой REST API для управления продуктами, партиями и доставками до клиента. 
Выполнено с фреймворком FastApi, БД Postgresql с помощью асинхронных вызовов, Alembic миграциями и Redis для кеширования.

1. Клонировать репозиторий и перейти в него:

    ```bash
    git clone https://github.com/kirillkiselev-slim/etalon_storage
    cd etalon_storage
    ```
   
2. Создать свой .env файл с помощью команд ниже и заполните его. Файл .env.example может послужить примером.

Для Linux/Mac
```bash
touch .env
```

Для Windows
```commandline
type nul > .env2
```

Запустить Docker Compose для сборки и запуска контейнеров Postgresql и FastApi приложения:

   ```bash
    docker compose up --build -d
   ```
   
Это автоматически соберет образы и запустит контейнеры для PostgreSQL и backend-приложения.

## Примеры запросов

### 1-й пример

**Method:** `POST`  
**Endpoint:** `/api/v1/production_batches/` - заливаем партию на нашем производстве

**Body:**

```json
{
  "product_id": "7bcd4f88-2f61-4815-91e0-d84b8a6c8a45",
  "start_date": "2024-11-15T13:55:36.232Z",
  "quantity_in_batch": 1
}
```
**start_date** дефолтное текущее время (лучше оставить его)
**product_id** можно найти через эндпоинт `/api/v1/products/` (формат UUID, но по факту str, так как сериализовать было проще str)

**Response:**

```json
{
  "id": 3,
  "product_id": 2,
  "start_date": "2024-11-15T13:55:54.520000+00:00",
  "current_stage": "INITIALIZED",
  "quantity_to_be_produced": 1,
  "product_model": "SkyDrive Elite"
}
```

### 2-й пример

**Method:** `PUT`  
**Endpoint:** `/api/v1/warehouse/receive-batch/{batch_id}` - принимаем партию на складе (используем 3 партию из примера выше)

**Body:**

```json
{
  "storage_location": "A1",
  "quantity_received": 1
}
```

**Response:**

```json
{
  "message": "Batch received successfully.",
  "received_batch": {
    "id": 2,
    "product_id": 2,
    "storage_location": "A1",
    "stock_quantity": 1
  }
}

```

**Possible user errors**

Наша партия еще не завершена:
```json
{
  "detail": {
    "error": "batch is not in \"COMPLETED\" stage yet!"
  }
}

```
Такой партии не существует: 
```json
{
  "detail": "ProductionBatches with ID 45 is not found"
}
```

Партия уже была добавлена на наш склад:
```json
{
  "detail": {
    "error": "batch has been already added!"
  }
}
```

**Method:** `PUT`  
**Endpoint:** `/api/v1/warehouse/shipments` - отправляем партию клиенту (используем 3 партию из примера выше)

```json

{
  "status": "PENDING",
  "items": [
    {
      "batch_id": 3
    }
  ]
}
```

**Response**

```json
{
  "shipment_id": 2,
  "order_id": "ORD126427",
  "items": [
    {
      "batch_id": 3
    }
  ],
  "status": "PENDING"
}
```

**Possible user errors**

Одна из наших партий не найдена 
```json
{
  "detail": "One or more batch IDs do not exist"
}
```
Наша партия уже отправлена:
```json
{
  "detail": "One or more batches have already been added in shipments"
}
```

### Валидация и логика:

~~~
1. Когда вы запускаете docker compose, файл init.sql должен автоматически выполниться для загрузки продуктов.
2. При отправке партий в БД меняются поля in_shipment=True, stock_quantity=0 (in_shipment поле больше для разрабочиков).
3. Статусы могут быть только в определенных статусах.
4. Мы не можем принять партию, если она не выполнена.
~~~

### Улучшения или баги
- Возможно стоит пересмотреть изменения полей in_shipment и stock_quantity, потому что нам могут 
завести больше кол-во товаров и мы можем клиенту отправить больше, а не нужное кол-во. Соответственно, убытки для нашего бизнеса, 
так как мы произвели одно кол-во, а отправили другое. И то же самое действует в другую сторону, только клиент будет разочарован.
- Сделать поле `product_id` по-другому, чтобы тратить меньше ресурсов, так как формат UUID, а фактически это String.

### Использованные технологии

* Python 3.12
* FastApi 0.115.4
* Aioredis 2.0.1
* Alembic 1.14.0
* SQLAlchemy 2.0.36
* Docker
* Docker-compose
* Postgres

### Автор

[Кирилл Киселев](https://github.com/kirillkiselev-slim)
