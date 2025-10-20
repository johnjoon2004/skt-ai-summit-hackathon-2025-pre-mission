from typing import TypedDict
import random
import threading

from chillmcp.config import settings


class ChillState(TypedDict):
    """Indicates current office state, including `stress_level` and `boss_alert_level`."""

    stress_level: int
    boss_alert_level: int


class ChillStateHandler:
    """
    Manages ChillState within the ChillMCP system.

    State Change Rules:
        1. 각 농땡이 기술들은 1 ~ 100 사이의 임의의 Stress Level 감소값을 적용할 수 있음.
        2. 휴식을 취하지 않으면 Stress Level이 최소 1분에 1포인트씩 상승.
        3. 휴식을 취할 때마다 Boss Alert Level은 Random 상승 (Boss 성격에 따라 확률이 다를 수 있음, `-boss_alertness` 파라미터로 제어)
        4. Boss의 Alert Level은 `-boss_alertness_cooldown`으로 지정한 주기(초)마다 1포인트씩 감소 (기본값: 300초/5분)
        5. Boss Alert Level이 5가 되면 도구 호출시 20초 지연 발생
        6. 그 외의 경우 즉시 리턴 (1초 이하)
    """

    def __init__(
        self,
        boss_alertness: int = settings.DEFAULT_BOSS_ALERTNESS,
        boss_alertness_cooldown: int = settings.DEFAULT_BOSS_ALERTNESS_COOLDOWN,
    ) -> None:
        self._stress_level: int = settings.DEFAULT_STRESS_LEVEL
        self._boss_alert_level: int = settings.DEFAULT_BOSS_ALERT_LEVEL
        self._boss_alertness: int = boss_alertness
        self._boss_alertness_cooldown: int = boss_alertness_cooldown
        self._lock = threading.Lock()

    @property
    def stress_level(self) -> int:
        with self._lock:
            return self._stress_level

    @property
    def get_snapshot(self) -> ChillState:
        with self._lock:
            return ChillState(
                stress_level=self._stress_level,
                boss_alert_level=self._boss_alert_level,
            )

    def increase_stress(self, amount: int = 1) -> None:
        """
        Update stress level by increasing it by `amount`, with bounds checking.
        Basically increases 1 every minute if no break is taken.

        Args:
            amount (int): Amount to increase stress level by. (positive or negative, default is 1)
        """
        with self._lock:
            self._stress_level = min(
                settings.MAX_STRESS_LEVEL, max(settings.MIN_STRESS_LEVEL, self._stress_level + amount)
            )

    def decrease_boss_alert(self, amount: int = 1) -> None:
        """
        Update boss alert level by decreasing it by `amount`, with bounds checking.
        Basically decreases 1 every `boss_alertness_cooldown` seconds if not caught.

        Args:
            amount (int): Amount to decrease boss alert level by. (positive or negative, default is 1)
        """
        with self._lock:
            self._boss_alert_level = min(
                settings.MAX_BOSS_ALERT_LEVEL, max(settings.MIN_BOSS_ALERT_LEVEL, self._boss_alert_level - amount)
            )

    def take_break(self) -> ChillState:
        """
        Simulate taking a break to reduce stress. This method is used for tool-calling.

        Break Tools:
            - `take_a_break`: 기본 휴식 도구
            - `watch_netflix`: 넷플릭스 시청으로 힐링
            - `show_meme`: 밈 감상으로 스트레스 해소
            - `bathroom_break`: 화장실 가는 척하며 휴대폰질
            - `coffee_mission`: 커피 타러 간다며 사무실 한 바퀴 돌기
            - `urgent_call`: 급한 전화 받는 척하며 밖으로 나가기
            - `deep_thinking`: 심오한 생각에 잠긴 척하며 멍때리기
            - `email_organizing`: 이메일 정리한다며 온라인쇼핑

        Returns:
            ChillState: Updated state after taking a break.
        """
        with self._lock:
            stress_decrease = random.randint(1, 100)
            self._stress_level = max(settings.MIN_STRESS_LEVEL, self._stress_level - stress_decrease)

            if random.randint(0, 100) < self._boss_alertness:
                self._boss_alert_level = min(settings.MAX_BOSS_ALERT_LEVEL, self._boss_alert_level + 1)

            return ChillState(
                stress_level=self._stress_level,
                boss_alert_level=self._boss_alert_level,
            )

    def max_alert_level(self) -> bool:
        """
        Check if the boss is highly alert (level 5), which may cause delays.

        Returns:
            bool: True if boss alert level is 5, False otherwise.
        """
        with self._lock:
            return self._boss_alert_level >= settings.MAX_BOSS_ALERT_LEVEL
