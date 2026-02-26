from dataclasses import dataclass, field


@dataclass
class AppConfig:
    expiry_days: int = 7
    llm_retry_count: int = 3
    llm_quota_backoff_sec: int = 25
    currencies: list[str] = field(default_factory=lambda: ["AMD", "USD", "EUR", "RUB"])


config = AppConfig()
