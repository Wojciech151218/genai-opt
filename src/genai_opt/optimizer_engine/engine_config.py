from __future__ import annotations

class EngineConfig:
    _instance: "EngineConfig | None" = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        population_size: int = 100,
    ):
        if getattr(self, "_initialized", False):
            return
        self.max_population_size = population_size
        self._initialized = True
