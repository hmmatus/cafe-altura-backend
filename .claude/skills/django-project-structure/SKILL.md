---
name: django-project-structure
description: Use when creating a file in this Django backend, deciding which directory code belongs in, adding a model/service/view/repository, reviewing a diff for layering problems, or when an import appears to cross a layer boundary.
---

# Django Project Structure (Clean Architecture)

## Overview

This backend is built so the business logic survives the framework. Django, DRF, and
PostgreSQL are replaceable details; `domain/` and `application/` are the product.

**Core principle: dependencies point inward.** Inner layers never know about outer ones.

```
interface/  ──┐
              ├──> application/ ──> domain/
infrastructure/ ┘
```

`domain` imports nothing. `application` imports `domain`. `infrastructure` and `interface`
import both. Nothing imports `interface` or `infrastructure` except the composition root.

## Directory Tree

```
config/                          # Django wiring ONLY — settings, urls, container
    settings.py
    urls.py
    container.py                 # composition root: builds concrete deps
domain/                          # ZERO framework imports
    <context>/
        entities.py              # plain dataclasses, invariants, behaviour
        value_objects.py
        exceptions.py            # domain errors, no HTTP status codes
application/                     # ZERO framework imports
    <context>/
        interfaces.py            # ABC ports: repositories, gateways
        services.py              # use cases, one class per use case
        dtos.py                  # input/output shapes for use cases
infrastructure/                  # Django allowed
    db/
        apps.py                  # Django app: label "db"
        models/<context>.py      # Django ORM models (persistence shape)
        repositories/<context>.py# implements application interfaces
        migrations/
    external/<service>.py        # HTTP clients, payment gateways, email
interface/                       # Django + DRF allowed
    api/<context>/
        serializers.py           # request validation + response shaping
        views.py                 # HTTP only, no business logic
        urls.py
manage.py
```

`<context>` is a business area (`orders`, `products`, `customers`) — never a technical
grouping (`utils`, `common`, `helpers`).

## Layer Rules

| Layer | May import | Must NOT contain |
|---|---|---|
| `domain` | stdlib only | `django`, `rest_framework`, ORM, HTTP, SQL |
| `application` | `domain`, stdlib, `abc` | `django`, `rest_framework`, concrete repos |
| `infrastructure` | `application`, `domain`, django | business rules, HTTP status codes |
| `interface` | `application`, `domain`, django, DRF | business rules, ORM queries, `.objects` |

**The ORM model is not the entity.** `infrastructure/db/models/order.py` holds an
`OrderModel` shaped for storage. `domain/orders/entities.py` holds an `Order` shaped for
business rules. Repositories translate between them.

## Core Pattern

Port in `application`, adapter in `infrastructure`:

```python
# application/orders/interfaces.py  — no Django
from abc import ABC, abstractmethod
from domain.orders.entities import Order

class OrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> Order: ...

    @abstractmethod
    def get(self, order_id: str) -> Order | None: ...
```

```python
# infrastructure/db/repositories/orders.py  — Django lives here
from application.orders.interfaces import OrderRepository
from domain.orders.entities import Order
from infrastructure.db.models.orders import OrderModel

class DjangoOrderRepository(OrderRepository):
    def add(self, order: Order) -> Order:
        row = OrderModel.objects.create(id=order.id, total=order.total)
        return self._to_entity(row)

    def get(self, order_id: str) -> Order | None:
        row = OrderModel.objects.filter(id=order_id).first()
        return self._to_entity(row) if row else None

    @staticmethod
    def _to_entity(row: OrderModel) -> Order:
        return Order(id=str(row.id), total=row.total)
```

Services receive ports through the constructor — never import a concrete class:

```python
# application/orders/services.py
class CreateOrder:
    def __init__(self, orders: OrderRepository, payments: PaymentGateway):
        self._orders = orders
        self._payments = payments
```

Concrete wiring happens once, in `config/container.py`.

## Settings

Register `infrastructure.db` in `INSTALLED_APPS` so migrations work. Do not create Django
apps for `domain` or `application` — they are plain Python packages.

## Common Mistakes

| Mistake | Fix |
|---|---|
| `from infrastructure...` inside `application/` or `domain/` | Depend on the ABC port; inject the concrete class at the container |
| Django model used as the domain entity | Add a dataclass entity; map it in the repository |
| `Model.objects.filter(...)` inside a view | Move the query behind a repository method |
| Business rule inside a serializer (`validate_*` doing pricing, stock, permissions) | Serializers check *shape*; services check *rules* |
| Repository returns a `QuerySet` | Return entities or lists of entities |
| Service raises `ValidationError` / returns `Response` | Raise a domain exception; the view maps it to HTTP |
| `domain/shared/utils.py` grab-bag | Name by business context, or make it a value object |

## Verification

```bash
# no framework leakage into the inner layers — must print nothing
grep -rnE '^\s*(from|import)\s+(django|rest_framework)' domain/ application/

# no inward-pointing violation — must print nothing
grep -rnE '^\s*(from|import)\s+(infrastructure|interface)' domain/ application/

.venv/bin/python manage.py check
```
