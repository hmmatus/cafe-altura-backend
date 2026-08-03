---
name: django-endpoint-creator
description: Use when adding or changing an API endpoint, route, REST resource, or DRF view in this Django backend, including "expose X over HTTP", "add a POST for Y", or "the frontend needs an endpoint for Z".
---

# Creating an Endpoint (Clean Architecture)

## Overview

An endpoint is the last thing you build, not the first. The use case exists without HTTP;
the view is a thin adapter that translates HTTP into a use-case call.

**REQUIRED BACKGROUND:** Use `django-project-structure` for layer boundaries and the
directory tree. This skill is the ordered recipe.

## Build Order

Build inward-out. Each step only depends on steps above it, so each one is testable alone.

1. **Domain** — `domain/<context>/entities.py`, `exceptions.py`
   Entity as a dataclass, invariants enforced in `__post_init__` or behaviour methods.
   Domain errors are domain classes (`OrderNotFound`), never `Http404` or DRF exceptions.

2. **Port** — `application/<context>/interfaces.py`
   Add only the ABC methods this use case needs. Do not design a full CRUD port up front.

3. **Use case** — `application/<context>/services.py`
   One class, one public `execute()`. Dependencies via `__init__`. Takes and returns DTOs
   or entities — never `request`, `Response`, or a serializer.

4. **Persistence** — `infrastructure/db/models/<context>.py` + migration
   `.venv/bin/python manage.py makemigrations && .venv/bin/python manage.py migrate`

5. **Adapter** — `infrastructure/db/repositories/<context>.py`
   Implements the port, maps rows to entities.

6. **Wiring** — `config/container.py`
   One provider function per use case. The only place concrete classes are named.

7. **HTTP** — `interface/api/<context>/serializers.py`, `views.py`, `urls.py`
   Serializer validates shape. View calls the use case, maps domain exceptions to status
   codes. No `.objects`, no rules.

8. **Route** — include the context urls in `config/urls.py` under `api/`.

## Worked Example

```python
# 3. application/orders/services.py
from application.orders.interfaces import OrderRepository
from domain.orders.entities import Order

class CreateOrder:
    def __init__(self, orders: OrderRepository):
        self._orders = orders

    def execute(self, customer_id: str, total: Decimal) -> Order:
        order = Order.draft(customer_id=customer_id, total=total)  # invariants here
        return self._orders.add(order)
```

```python
# 6. config/container.py
from application.orders.services import CreateOrder
from infrastructure.db.repositories.orders import DjangoOrderRepository

def create_order() -> CreateOrder:
    return CreateOrder(orders=DjangoOrderRepository())
```

```python
# 7. interface/api/orders/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config import container
from domain.orders.exceptions import OrderInvalid
from interface.api.orders.serializers import CreateOrderSerializer, OrderSerializer

class CreateOrderView(APIView):
    def post(self, request):
        payload = CreateOrderSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        try:
            order = container.create_order().execute(**payload.validated_data)
        except OrderInvalid as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
```

```python
# 7. interface/api/orders/urls.py
urlpatterns = [path("orders/", CreateOrderView.as_view(), name="orders-create")]
```

## Exception Mapping

Domain exceptions carry meaning; the view owns the status code.

| Domain exception | HTTP |
|---|---|
| `<X>NotFound` | 404 |
| `<X>Invalid`, broken invariant | 422 |
| `<X>Conflict`, duplicate | 409 |
| `NotAllowed` | 403 |
| serializer `is_valid` failure | 400 (DRF default) |

## Tests

Write the use-case test first — it needs no database and no HTTP.

- **Use case:** instantiate with a fake in-memory repository implementing the port. Assert
  entities and raised domain exceptions.
- **Repository:** `TestCase` with the real DB; assert entity ↔ row mapping round-trips.
- **View:** `APIClient`; assert status codes and payload shape only.

A use-case test that needs `manage.py migrate` or `APIClient` means logic leaked outward.

## Red Flags

- Writing `views.py` first
- Serializer with a `validate_*` method that applies a business rule
- `Model.objects` anywhere under `interface/`
- Use case importing `rest_framework`, `request`, or a serializer
- Use case returning a `Response` or a `dict` shaped for JSON
- New concrete repository named outside `config/container.py`
- Adding a port method the current use case does not call

**Any of these mean: stop and rebuild inward-out from step 1.**

## Verification

```bash
grep -rnE '^\s*(from|import)\s+(django|rest_framework)' domain/ application/   # empty
grep -rn '\.objects' interface/                                               # empty
.venv/bin/python manage.py check && .venv/bin/python manage.py test
```
