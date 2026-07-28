# Application layer

Use cases orchestrate the domain and depend only on **ports** (interfaces),
never on concrete adapters.

- `use_cases/` — RecordDepositUseCase, CloseMonthlyPeriodUseCase, RequestOtpUseCase.
- `ports/` — TransactionRepository, NotificationSender, OtpStore, IdempotencyStore,
  Clock, UnitOfWork. Infrastructure provides the implementations.
