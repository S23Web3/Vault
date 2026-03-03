"""
Strategy adapter: loads plugin, orchestrates signal flow on new bars.
"""
import importlib
import logging
from ttp_engine import TTPExit

logger = logging.getLogger(__name__)


class StrategyAdapter:
    """Load strategy plugin and drive signal-to-execution pipeline."""

    def __init__(self, plugin_name, risk_gate, executor,
                 state_manager, notifier, plugin_config=None,
                 ttp_config=None):
        """Initialize with plugin name and downstream components."""
        self.plugin = self._load_plugin(plugin_name, plugin_config)
        self.risk_gate = risk_gate
        self.executor = executor
        self.state_manager = state_manager
        self.notifier = notifier
        self.warmup_needed = self.plugin.warmup_bars()
        self.allowed_grades = self.plugin.get_allowed_grades()
        # TTP configuration
        _ttp = ttp_config or {}
        self.ttp_enabled = _ttp.get("ttp_enabled", False)
        self.ttp_act = _ttp.get("ttp_act", 0.005)
        self.ttp_dist = _ttp.get("ttp_dist", 0.002)
        self.ttp_engines = {}  # keyed by position key e.g. "BTCUSDT_LONG"
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
        # --- Signal processing ---
        try:
            signal = self.plugin.get_signal(ohlcv_df)
        except Exception as e:
            logger.error("Plugin error %s: %s", symbol, e)
            signal = None
        if signal is not None and signal.direction != "NONE":
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
            else:
                result = self.executor.execute(signal, symbol)
                if result is None:
                    logger.error("Execution failed: %s %s",
                                  signal.direction, symbol)
        # --- TTP evaluation (always runs after warmup, even without signal) ---
        self._evaluate_ttp_for_symbol(symbol, ohlcv_df)

    def _evaluate_ttp_for_symbol(self, symbol, ohlcv_df):
        """Evaluate TTP trailing exit for any open position matching this symbol."""
        if not self.ttp_enabled:
            return
        try:
            latest = ohlcv_df.iloc[-1]
            h = float(latest["high"])
            l = float(latest["low"])
        except (IndexError, KeyError, TypeError):
            return
        positions = self.state_manager.get_state().get("open_positions", {})
        # Prune engines for closed positions
        stale = [k for k in self.ttp_engines if k not in positions]
        for k in stale:
            del self.ttp_engines[k]
        for key, pos in positions.items():
            if pos.get("symbol") != symbol:
                continue
            engine = self.ttp_engines.get(key)
            if engine is None:
                engine = TTPExit(
                    pos.get("direction", "LONG"),
                    pos.get("entry_price", 0),
                    self.ttp_act,
                    self.ttp_dist,
                )
                self.ttp_engines[key] = engine
            if engine.state == "CLOSED":
                continue
            result = engine.evaluate(candle_high=h, candle_low=l)
            self.state_manager.update_position(key, {
                "ttp_state": engine.state,
                "ttp_trail_level": engine.trail_level,
                "ttp_extreme": engine.extreme,
            })
            if result.closed_pessimistic:
                self.state_manager.update_position(key, {
                    "ttp_close_pending": True,
                    "ttp_exit_pct_pess": result.exit_pct_pessimistic,
                    "ttp_exit_pct_opt": result.exit_pct_optimistic,
                })
                logger.info("TTP close pending: %s pess=%.4f%%",
                            key, (result.exit_pct_pessimistic or 0) * 100)
