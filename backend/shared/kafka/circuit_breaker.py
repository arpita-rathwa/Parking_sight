import time
import logging
from enum import Enum
from threading import Lock

logger = logging.getLogger("kafka.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        half_open_max_attempts: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_max_attempts = half_open_max_attempts

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_attempts = 0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.cooldown_seconds:
                    logger.info("Circuit breaker transitioning OPEN -> HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_attempts = 0
            return self._state

    def try_request(self) -> bool:
        state = self.state
        if state == CircuitState.OPEN:
            return False
        return True

    def on_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_attempts += 1
                if self._half_open_attempts >= self.half_open_max_attempts:
                    logger.info(
                        "Circuit breaker HALF_OPEN -> CLOSED after %d successes",
                        self._half_open_attempts,
                    )
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_attempts = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    "Circuit breaker HALF_OPEN -> OPEN (failure %d)",
                    self._failure_count,
                )
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.failure_threshold:
                logger.warning(
                    "Circuit breaker CLOSED -> OPEN (threshold %d reached)",
                    self.failure_threshold,
                )
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = 0.0
            self._half_open_attempts = 0
            logger.info("Circuit breaker reset to CLOSED")
