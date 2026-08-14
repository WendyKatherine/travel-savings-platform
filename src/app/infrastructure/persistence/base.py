"""
base.py - Declarative base shared by every ORM model.

Alembic uses ``Base.metadata`` as ``target_metadata`` so autogenerate
can diff the models against the database. The naming convention keeps
constraint names deterministic and stable across migrations.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

class Base(DeclarativeBase):
    """Declarative base for the persistence layer.

    All ORM models inherit from this class so their tables are
    registered on ``Base.metadata`` for Alembic autogenerate.
    """

    metadata = metadata_obj