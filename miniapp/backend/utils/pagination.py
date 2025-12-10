from typing import Generic, List, Tuple, TypeVar

from pydantic import BaseModel

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

T = TypeVar("T")


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: Pagination


def sanitize_pagination(page: int | None, limit: int | None) -> Tuple[int, int, int]:
    """Return safe page/limit values and the computed offset."""
    safe_limit = DEFAULT_LIMIT if not limit or limit <= 0 else min(limit, MAX_LIMIT)
    safe_page = 1 if not page or page <= 0 else page
    offset = (safe_page - 1) * safe_limit
    return safe_page, safe_limit, offset


def paginate(items: List[T], total: int, page: int, limit: int) -> PaginatedResponse[T]:
    """Build a standardized pagination envelope."""
    _, limit_value, offset = sanitize_pagination(page, limit)
    return PaginatedResponse(
        data=items,
        pagination=Pagination(
            total=total,
            limit=limit_value,
            offset=offset,
            has_more=offset + len(items) < total,
        ),
    )
