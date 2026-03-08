from supabase import create_client, Client

from app.config import settings

_supabase: Client | None = None


def get_supabase() -> Client | None:
    """Return the Supabase client if configured, else None."""
    global _supabase
    if _supabase is not None:
        return _supabase
    if settings.supabase_url and settings.supabase_anon_key:
        _supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        return _supabase
    return None


def get_supabase_required() -> Client:
    """Return the Supabase client or raise RuntimeError if not configured."""
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
    return client
