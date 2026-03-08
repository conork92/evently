from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Same as other Supabase apps (e.g. HighgateAvenue). No region or DB URL needed.
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    # Optional: for "Add by link" – fetch Songkick event by ID. Get key at https://www.songkick.com/developer
    songkick_api_key: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
