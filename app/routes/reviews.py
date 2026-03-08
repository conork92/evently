from fastapi import APIRouter, Depends, HTTPException

from supabase import Client

from app import schemas_review
from app.crud_review import (
    create_review,
    delete_review,
    get_review,
    list_reviews,
    update_review,
)
from app.supabase_client import get_supabase

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def _require_supabase() -> Client:
    client = get_supabase()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.",
        )
    return client


@router.post("/", response_model=schemas_review.ReviewRead)
def create(r: schemas_review.ReviewCreate, supabase: Client = Depends(_require_supabase)):
    row = create_review(supabase, r.model_dump())
    return schemas_review.ReviewRead.model_validate(row)


@router.get("/", response_model=list[schemas_review.ReviewRead])
def list_all(supabase: Client = Depends(_require_supabase)):
    rows = list_reviews(supabase)
    return [schemas_review.ReviewRead.model_validate(r) for r in rows]


@router.get("/{review_id}", response_model=schemas_review.ReviewRead)
def get(review_id: int, supabase: Client = Depends(_require_supabase)):
    row = get_review(supabase, review_id)
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
    return schemas_review.ReviewRead.model_validate(row)


@router.patch("/{review_id}", response_model=schemas_review.ReviewRead)
def update(
    review_id: int,
    data: schemas_review.ReviewUpdate,
    supabase: Client = Depends(_require_supabase),
):
    row = update_review(supabase, review_id, data)
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
    return schemas_review.ReviewRead.model_validate(row)


@router.delete("/{review_id}", status_code=204)
def delete(review_id: int, supabase: Client = Depends(_require_supabase)):
    if not delete_review(supabase, review_id):
        raise HTTPException(status_code=404, detail="Review not found")
