from typing import TypedDict
import random
import threading
import time

from chillmcp.config import settings


class ChillState(TypedDict):
    stress_level: int
    boss_alert_level: int


class ChillStateManager:
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
    ):
        """
        Args:
            boss_alertness (int): Boss alertness level (0-100) affecting alert level increase probability.
            boss_alertness_cooldown (int): Cooldown time in seconds for decreasing boss alert level.
        """
        self._stress_level: int = settings.DEFAULT_STRESS_LEVEL
        self._boss_alert_level: int = settings.DEFAULT_BOSS_ALERT_LEVEL
        self._boss_alertness: int = self._clamp(
            boss_alertness,
            settings.MIN_BOSS_ALERTNESS,
            settings.MAX_BOSS_ALERTNESS,
        )
        self._boss_alertness_cooldown: int = boss_alertness_cooldown

        self._lock = threading.Lock()
        self._stress_timer: threading.Timer | None = None
        self._boss_alert_timer: threading.Timer | None = None
        self._is_running: bool = True

        self._start_stress_timer()
        self._start_boss_alert_timer()

    def _clamp(self, val, lower, upper):
        return max(lower, min(upper, val))

    def _start_stress_timer(self):
        self._stress_timer = threading.Timer(settings.STRESS_INCREASE_INTERVAL, self._increase_stress)
        self._stress_timer.daemon = True  # NOTE: do not set False
        self._stress_timer.start()

    def _start_boss_alert_timer(self):
        self._boss_alert_timer = threading.Timer(self._boss_alertness_cooldown, self._decrease_boss_alert)
        self._boss_alert_timer.daemon = True  # NOTE: do not set False
        self._boss_alert_timer.start()

    def _increase_stress(self):
        with self._lock:
            if self._stress_level < settings.MAX_STRESS_LEVEL:
                self._stress_level += 1
        if self._is_running:
            self._start_stress_timer()  # reschedule the timer

    def _decrease_boss_alert(self):
        with self._lock:
            if self._boss_alert_level > settings.MIN_BOSS_ALERT_LEVEL:
                self._boss_alert_level -= 1
        if self._is_running:
            self._start_boss_alert_timer()  # reschedule the timer

    def shutdown(self):
        self._is_running = False
        if self._stress_timer:
            self._stress_timer.cancel()
        if self._boss_alert_timer:
            self._boss_alert_timer.cancel()

    @property
    def current_state(self) -> ChillState:
        with self._lock:
            return ChillState(
                stress_level=self._stress_level,
                boss_alert_level=self._boss_alert_level,
            )

    def take_a_break(self) -> tuple[int, int]:
        """
        Simulates taking a break, updating stress and boss alert levels.
        This method handles the delay when the boss alert level is at maximum.

        Returns:
            Tuple[int, int]: The new stress_level and boss_alert_level.
        """
        with self._lock:
            # Boss Alert Level 5: Induce a 20-second delay
            if self._boss_alert_level >= settings.MAX_BOSS_ALERT_LEVEL:
                time.sleep(settings.MAX_ALERT_DELAY)

            # Decrease stress level by a random amount
            stress_reduction = random.randint(1, 100)
            self._stress_level = self._clamp(
                self._stress_level - stress_reduction,
                settings.MIN_STRESS_LEVEL,
                settings.MAX_STRESS_LEVEL,
            )

            # Potentially increase boss alert level based on boss_alertness
            if random.randint(1, 100) <= self._boss_alertness:
                self._boss_alert_level = self._clamp(
                    self._boss_alert_level + 1,
                    settings.MIN_BOSS_ALERT_LEVEL,
                    settings.MAX_BOSS_ALERT_LEVEL,
                )

            return self._stress_level, self._boss_alert_level


# Singleton instance
state_handler_instance: ChillStateManager | None = None
state_handler_lock = threading.Lock()
