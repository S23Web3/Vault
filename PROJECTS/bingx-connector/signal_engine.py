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
        self.ttp_act = _ttp.get("ttp_act", 0.008)
        self.ttp_dist = _ttp.get("ttp_dist", 0.003)
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
            entry = pos.get("entry_price", 0) or 0
            engine = self.ttp_engines.get(key)
            if engine is None:
                if not entry:
                    logger.warning("TTP: skipping %s — no entry_price in state", key)
                    continue
                # Per-position TTP overrides from dashboard "Set TTP"
                pos_act = pos.get("ttp_act_override", self.ttp_act)
                pos_dist = pos.get("ttp_dist_override", self.ttp_dist)
                engine = TTPExit(
                    pos.get("direction", "LONG"),
                    entry,
                    pos_act,
                    pos_dist,
                )
                # Restore persisted TTP state on bot restart
                saved_state = pos.get("ttp_state", "MONITORING")
                saved_extreme = pos.get("ttp_extreme")
                saved_trail = pos.get("ttp_trail_level")
                if saved_state == "ACTIVATED" and saved_extreme and saved_trail:
                    engine.state = "ACTIVATED"
                    engine.extreme = float(saved_extreme)
                    engine.trail_level = float(saved_trail)
                    logger.info(
                        "TTP restored: %s state=ACTIVATED extreme=%.8f trail=%.8f",
                        key, engine.extreme, engine.trail_level)
                elif saved_state == "CLOSED":
                    engine.state = "CLOSED"
                    logger.info("TTP restored: %s state=CLOSED (skipping)", key)
                self.ttp_engines[key] = engine
            # Dashboard "Activate Now" — force to ACTIVATED from last candle extreme
            if pos.get("ttp_force_activate") and engine.state == "MONITORING":
                engine.state = "ACTIVATED"
                engine.extreme = h if pos.get("direction", "LONG") == "LONG" else l
                if pos.get("direction", "LONG") == "LONG":
                    engine.trail_level = engine.extreme * (1.0 - engine.dist)
                else:
                    engine.trail_level = engine.extreme * (1.0 + engine.dist)
                logger.info("TTP force-activated: %s extreme=%.8f trail=%.8f",
                            key, engine.extreme, engine.trail_level)
                self.state_manager.update_position(key, {
                    "ttp_force_activate": False,
                    "ttp_state": "ACTIVATED",
                    "ttp_trail_level": engine.trail_level,
                    "ttp_extreme": engine.extreme,
                })
            # Dashboard "Set TTP" with dirty flag — recreate engine with new params
            if pos.get("ttp_engine_dirty"):
                pos_act = pos.get("ttp_act_override", self.ttp_act)
                pos_dist = pos.get("ttp_dist_override", self.ttp_dist)
                new_engine = TTPExit(
                    pos.get("direction", "LONG"),
                    entry,
                    pos_act,
                    pos_dist,
                )
                self.ttp_engines[key] = new_engine
                engine = new_engine
                self.state_manager.update_position(key, {
                    "ttp_engine_dirty": False,
                    "ttp_state": "MONITORING",
                    "ttp_trail_level": None,
                    "ttp_extreme": None,
                })
                logger.info("TTP engine recreated: %s act=%.4f dist=%.4f",
                            key, pos_act, pos_dist)
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
