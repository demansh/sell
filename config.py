from dataclasses import dataclass, field


@dataclass
class AppConfig:
    expiry_days: int = 7
    llm_retry_count: int = 3
    llm_quota_backoff_sec: int = 25
    categories: list[str] = field(default_factory=lambda: [
        "electronics",
        "computers",
        "mobile",
        "furniture",
        "toys",
        "music",
        "arts",
        "jewelry",
        "clothing",
        "sport",
        "home",
        "transport",
        "hobbies",
        "watches",
        "other",
    ])
    currencies: list[str] = field(default_factory=lambda: ["AMD", "USD", "EUR", "RUB"])


config = AppConfig()
