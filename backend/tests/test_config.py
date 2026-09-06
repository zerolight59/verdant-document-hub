from app.core.config import Settings


def test_database_url_is_built_from_separate_postgresql_settings():
    settings = Settings(
        _env_file=None,
        verdant_db_host="database.internal",
        verdant_db_port=5433,
        verdant_db_user="verdant user",
        verdant_db_password="p@ss/word",
        verdant_db_name="verdant_product",
        verdant_db_sslmode="require",
    )

    rendered = settings.database_url.render_as_string(hide_password=False)

    assert rendered.startswith("postgresql+psycopg://verdant user:p%40ss%2Fword@")
    assert "database.internal:5433/verdant_product" in rendered
    assert "sslmode=require" in rendered
