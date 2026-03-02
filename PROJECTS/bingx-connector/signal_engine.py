"""
Strategy adapter: loads plugin, orchestrates signal flow on new bars.
"""
import importlib
import logging

logger = logging.getLogger(__name__)


class StrategyAdapter:
    """Load strategy plugin and drive signal-to-execution pipeline."""

    def __init__(self, plugin_name, risk_gate, executor,
                 state_manager, notifier, plugin_config=None):
        """Initialize with plugin name and downstream components."""
        self.plugin = self._load_plugin(plugin_name, plugin_config)
        self.risk_gate = risk_gate
        self.executor = executor
        self.state_manager = state_manager
        self.notifier = notifier
        self.warmup_needed = self.plugin.warmup_bars()
        self.allowed_grades = self.plugin.get_allowed_grades()
        logger.info(
            "StrategyAdapter: plugin=%s v%s warmup=%d grades=%s",
            self.plugin.get_name(), self.plugin.get_version(),
            self.warmup_needed, str(self.allowed_grades))

    def _load_plugin(self, plugin_name, plugin_config=None):
        """Dynamically load a strategy plugin from plugins package."""
        try:
            module = importlib.import_module("plugins." + plugin_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type)
                        and hasattr(attr, "get_signal")
                        and attr_name != "Signal"):
                    instance = attr(config=plugin_config)
                    logger.info("Loaded plugin: %s (config=%s)",
                                attr_name,
                                "provided" if plugin_config else "defaults")
                    return instance
            raise ImportError(
                "No strategy class in plugins." + plugin_name)
        except ImportError as e:
            logger.error("Plugin load failed: %s", e)
            raise

    def on_new_bar(self, symbol, ohlcv_df):
        """Process a new confirmed bar through the signal pipeline."""
        if len(ohlcv_df) < self.warmup_needed + 1:
            logger.debug("Warmup: %s has %d/%d bars",
                         symbol, len(ohlcv_df), self.warmup_needed + 1)
            return
        try:
            signal = self.plugin.get_signal(ohlcv_df)
        except Exception as e:
            logger.error("Plugin error %s: %s", symbol, e)
            return
        if signal is None or signal.direction == "NONE":
            logger.debug("No signal: %s", symbol)
            return
        logger.info("Signal: %s %s grade=%s price=%.6f",
                     signal.direction, symbol,
                     signal.grade, signal.entry_price)
        state_dict = self.state_manager.get_state()
        approved, reason = self.risk_gate.evaluate(
            signal, symbol, state_dict, self.allowed_grades,
            state_manager=self.state_manager)
        if not approved:
            logger.info("Blocked: %s %s — %s",
                         signal.direction, symbol, reason)
            return
        result = self.executor.execute(signal, symbol)
        if result is None:
            logger.error("Execution failed: %s %s",
                          signal.direction, symbol)
