from pydantic_settings import BaseSettings


class ChillMCPSettings(BaseSettings):
    DEFAULT_STRESS_LEVEL: int = 50
    MIN_STRESS_LEVEL: int = 0
    MAX_STRESS_LEVEL: int = 100

    DEFAULT_BOSS_ALERT_LEVEL: int = 0
    MIN_BOSS_ALERT_LEVEL: int = 0
    MAX_BOSS_ALERT_LEVEL: int = 5

    DEFAULT_BOSS_ALERTNESS: int = 50  # Controllable parameter (runtime)
    MIN_BOSS_ALERTNESS: int = 0
    MAX_BOSS_ALERTNESS: int = 100

    DEFAULT_BOSS_ALERTNESS_COOLDOWN: int = 300  # Controllable parameter (runtime)

    STRESS_INCREASE_INTERVAL: int = 60  # stress-level 자동 증가 주기 (e.g. 1분)
    MAX_ALERT_DELAY: int = 20

    # Response parsing keys
    RESPONSE_BREAK_SUMMARY_KEY: str = "Break Summary"
    RESPONSE_STRESS_LEVEL_KEY: str = "Stress Level"
    RESPONSE_BOSS_ALERT_LEVEL_KEY: str = "Boss Alert Level"

    class Config:
        frozen = True
        env_prefix = "CHILLMCP_"


settings = ChillMCPSettings()
