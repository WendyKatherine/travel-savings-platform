# Domain layer

Pure Python. **No** imports from `infrastructure`, FastAPI, SQLAlchemy or Redis.

- `entities/` — objects with identity and lifecycle (SavingsPlan, Transaction).
- `value_objects/` — immutable values with invariants (Money).
- `services/` — pure domain logic that spans entities (balance calculation).

If a rule can only be tested by touching a database, it does not belong here.
