from sqlmodel import SQLModel, create_engine

from app.db.base import metadata


def test_all_models_create_tables_cleanly() -> None:
    engine = create_engine("sqlite://")
    metadata.create_all(engine)

    table_names = {table.name for table in metadata.sorted_tables}
    assert table_names == {
        "users",
        "client_profiles",
        "makeup_looks",
        "shade_items",
        "subscriptions",
        "enhance_usages",
        "enhance_jobs",
    }
