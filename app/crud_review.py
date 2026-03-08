from supabase import Client

from app import schemas_review

TABLE = "evently_reviews"


def create_review(supabase: Client, data: dict) -> dict:
    r = supabase.table(TABLE).insert(data).execute()
    rows = r.data or []
    return rows[0] if rows else data


def get_review(supabase: Client, review_id: int) -> dict | None:
    r = supabase.table(TABLE).select("*").eq("id", review_id).execute()
    rows = r.data or []
    return rows[0] if rows else None


def list_reviews(supabase: Client, limit: int = 50) -> list[dict]:
    r = supabase.table(TABLE).select("*").order("created_at", desc=True).limit(limit).execute()
    return r.data or []


def update_review(supabase: Client, review_id: int, data: schemas_review.ReviewUpdate) -> dict | None:
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return get_review(supabase, review_id)
    r = supabase.table(TABLE).update(payload).eq("id", review_id).execute()
    rows = r.data or []
    return rows[0] if rows else None


def delete_review(supabase: Client, review_id: int) -> bool:
    r = supabase.table(TABLE).delete().eq("id", review_id).execute()
    return bool(r.data and len(r.data) > 0)
