# Vault Code Manifest

- **Date:** 2026-02-14
- **Total:** 62
- **Active:** 62
- **Inactive:** 0

---

## Active Files

### `PROJECTS\four-pillars-backtester\data\fetcher.py`
- **Why:** imported by 10 files, recently modified
- **Modified:** 2026-02-12 15:20 | **Lines:** 252
- **Functions:** __init__, _cache_path, _meta_path, _fetch_page, fetch_symbol, fetch_multiple, load_cached, list_cached, __init__, to_api_symbol
- **Imports:** time, requests, pandas, pyarrow, pyarrow.parquet, pathlib, datetime, typing
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\dashboard.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v2.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py, PROJECTS\four-pillars-backtester\scripts\download_1year_gap_FIXED.py, PROJECTS\four-pillars-backtester\scripts\download_all_available.py, PROJECTS\four-pillars-backtester\scripts\download_periods.py, PROJECTS\four-pillars-backtester\scripts\download_periods_v2.py, PROJECTS\four-pillars-backtester\scripts\test_download_periods.py, PROJECTS\four-pillars-backtester\scripts\test_download_periods_v2.py

### `PROJECTS\four-pillars-backtester\data\normalizer.py`
- **Why:** imported by 8 files, recently modified
- **Modified:** 2026-02-12 20:30 | **Lines:** 542
- **Functions:** __init__, _detect_delimiter, _detect_columns, _detect_timestamp_format, _parse_timestamps, _detect_interval, _validate, resample_ohlcv, detect_format, normalize
- **Imports:** csv, io, pathlib, typing, numpy, pandas
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\convert_csv.py, PROJECTS\four-pillars-backtester\scripts\dashboard.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v2.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py, PROJECTS\four-pillars-backtester\scripts\test_normalizer.py

### `PROJECTS\four-pillars-backtester\data\period_loader.py`
- **Why:** imported by 2 files, recently modified
- **Modified:** 2026-02-13 12:07 | **Lines:** 123
- **Functions:** load_multi_period, list_available_symbols, get_symbol_coverage
- **Imports:** data.period_loader, pandas, pathlib, typing
- **Imported by:** PROJECTS\four-pillars-backtester\data\period_loader.py, PROJECTS\four-pillars-backtester\scripts\test_period_loader.py

### `PROJECTS\four-pillars-backtester\engine\avwap.py`
- **Why:** imported by 10 files, recently modified
- **Modified:** 2026-02-12 13:41 | **Lines:** 52
- **Functions:** __init__, update, bands, clone, freeze
- **Imports:** math
- **Imported by:** PROJECTS\four-pillars-backtester\engine\backtester_v383.py, PROJECTS\four-pillars-backtester\engine\backtester_v384.py, PROJECTS\four-pillars-backtester\engine\position_v382.py, PROJECTS\four-pillars-backtester\engine\position_v383.py, PROJECTS\four-pillars-backtester\engine\position_v384.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py

### `PROJECTS\four-pillars-backtester\engine\backtester_v382.py`
- **Why:** imported by 6 files, recently modified
- **Modified:** 2026-02-12 12:38 | **Lines:** 410
- **Functions:** __init__, run, _find_empty, _open_slot
- **Imports:** numpy, pandas, datetime, typing, .position_v382, .commission, .metrics
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\batch_sweep_v382.py, PROJECTS\four-pillars-backtester\scripts\batch_sweep_v382_be.py, PROJECTS\four-pillars-backtester\scripts\lsg_diagnostic_v382.py, PROJECTS\four-pillars-backtester\scripts\run_backtest_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py

### `PROJECTS\four-pillars-backtester\engine\backtester_v383.py`
- **Why:** imported by 7 files, recently modified
- **Modified:** 2026-02-12 14:33 | **Lines:** 579
- **Functions:** __init__, run, _find_empty, _open_slot, _compute_metrics, _trades_to_df
- **Imports:** numpy, pandas, datetime, typing, .position_v383, .commission, .avwap
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\capital_analysis_v383.py, PROJECTS\four-pillars-backtester\scripts\mfe_analysis_v383.py, PROJECTS\four-pillars-backtester\scripts\run_backtest_v383.py, PROJECTS\four-pillars-backtester\scripts\sweep_sl_mult_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\validation_v371_vs_v383.py

### `PROJECTS\four-pillars-backtester\engine\backtester_v384.py`
- **Why:** imported by 12 files, recently modified
- **Modified:** 2026-02-12 17:39 | **Lines:** 571
- **Functions:** __init__, run, _find_empty, _open_slot, _compute_metrics, _trades_to_df
- **Imports:** numpy, pandas, datetime, typing, .position_v384, .commission, .avwap
- **Imported by:** PROJECTS\four-pillars-backtester\engine\backtester_v385.py, PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\capital_analysis_v384.py, PROJECTS\four-pillars-backtester\scripts\dashboard.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v2.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py, PROJECTS\four-pillars-backtester\scripts\run_backtest_v384.py, PROJECTS\four-pillars-backtester\scripts\sweep_tp_v384.py, PROJECTS\four-pillars-backtester\scripts\test_sweep.py, PROJECTS\four-pillars-backtester\scripts\test_v385.py

### `PROJECTS\four-pillars-backtester\engine\backtester_v385.py`
- **Why:** imported by 4 files, recently modified
- **Modified:** 2026-02-13 16:36 | **Lines:** 379
- **Functions:** _safe_val, __init__, run, _extract_arrays, col, _snapshot_entry, _compute_lifecycle, _empty_lifecycle, _classify_pnl_path, _categorize_lsg
- **Imports:** os, numpy, pandas, typing, engine.backtester_v384, engine.position_v384
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py, PROJECTS\four-pillars-backtester\scripts\test_v385.py

### `PROJECTS\four-pillars-backtester\engine\commission.py`
- **Why:** imported by 4 files, recently modified
- **Modified:** 2026-02-12 14:33 | **Lines:** 112
- **Functions:** __init__, charge, charge_custom, check_settlement, net_commission
- **Imports:** datetime
- **Imported by:** PROJECTS\four-pillars-backtester\engine\backtester_v382.py, PROJECTS\four-pillars-backtester\engine\backtester_v383.py, PROJECTS\four-pillars-backtester\engine\backtester_v384.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py

### `PROJECTS\four-pillars-backtester\engine\metrics.py`
- **Why:** imported by 1 files, recently modified
- **Modified:** 2026-02-12 13:41 | **Lines:** 134
- **Functions:** compute_metrics, trades_to_dataframe
- **Imports:** numpy, pandas, typing
- **Imported by:** PROJECTS\four-pillars-backtester\engine\backtester_v382.py

### `PROJECTS\four-pillars-backtester\engine\position_v382.py`
- **Why:** imported by 3 files, recently modified
- **Modified:** 2026-02-12 12:37 | **Lines:** 225
- **Functions:** __init__, check_exit, update_bar, close_at
- **Imports:** dataclasses, typing, .avwap
- **Imported by:** PROJECTS\four-pillars-backtester\engine\backtester_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py

### `PROJECTS\four-pillars-backtester\engine\position_v383.py`
- **Why:** imported by 5 files, recently modified
- **Modified:** 2026-02-12 14:40 | **Lines:** 246
- **Functions:** __init__, check_exit, update_bar, check_scale_out, do_scale_out, close_at
- **Imports:** dataclasses, typing, .avwap
- **Imported by:** PROJECTS\four-pillars-backtester\engine\backtester_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py

### `PROJECTS\four-pillars-backtester\engine\position_v384.py`
- **Why:** imported by 3 files, recently modified
- **Modified:** 2026-02-12 17:37 | **Lines:** 295
- **Functions:** __init__, check_exit, update_bar, check_scale_out, do_scale_out, close_at
- **Imports:** dataclasses, typing, .avwap
- **Imported by:** PROJECTS\four-pillars-backtester\engine\backtester_v384.py, PROJECTS\four-pillars-backtester\engine\backtester_v385.py, PROJECTS\four-pillars-backtester\scripts\build_all_specs.py

### `PROJECTS\four-pillars-backtester\ml\coin_features.py`
- **Why:** imported by 2 files, recently modified
- **Modified:** 2026-02-13 16:36 | **Lines:** 115
- **Functions:** compute_coin_features, get_feature_names
- **Imports:** numpy, pandas, typing
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\test_vince_ml.py

### `PROJECTS\four-pillars-backtester\ml\features_v2.py`
- **Why:** imported by 3 files, recently modified
- **Modified:** 2026-02-13 12:07 | **Lines:** 334
- **Functions:** extract_trade_features, get_feature_columns
- **Imports:** numpy, pandas, typing
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py, PROJECTS\four-pillars-backtester\scripts\test_features_v2.py

### `PROJECTS\four-pillars-backtester\ml\training_pipeline.py`
- **Why:** imported by 2 files, recently modified
- **Modified:** 2026-02-13 16:38 | **Lines:** 182
- **Functions:** assign_pools, __init__, __len__, __getitem__, load_trade_parquets, prepare_labels, train_phase1
- **Imports:** os, json, random, numpy, pandas, torch, torch.nn, torch.utils.data, typing
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\test_vince_ml.py

### `PROJECTS\four-pillars-backtester\ml\vince_model.py`
- **Why:** imported by 2 files, recently modified
- **Modified:** 2026-02-13 16:36 | **Lines:** 148
- **Functions:** __init__, forward, __init__, forward, __init__, forward, __init__, forward, predict_tabular_only
- **Imports:** torch, torch.nn, numpy, typing
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\test_vince_ml.py

### `PROJECTS\four-pillars-backtester\ml\xgboost_auditor.py`
- **Why:** imported by 2 files, recently modified
- **Modified:** 2026-02-13 16:36 | **Lines:** 113
- **Functions:** __init__, train, compute_shap, get_top_features, compare_with_pytorch, get_feature_importance_df
- **Imports:** numpy, pandas, xgboost, shap, typing
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\test_vince_ml.py

### `PROJECTS\four-pillars-backtester\scripts\batch_sweep_v382.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 12:39 | **Lines:** 231
- **Functions:** list_5m_coins, load_5m, run_coin, format_batch_table, main
- **Imports:** argparse, random, sys, time, pathlib, datetime, pandas, signals.four_pillars_v382, engine.backtester_v382

### `PROJECTS\four-pillars-backtester\scripts\batch_sweep_v382_be.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 12:41 | **Lines:** 231
- **Functions:** list_5m_coins, load_5m, run_coin, main
- **Imports:** argparse, random, sys, time, numpy, pathlib, pandas, signals.four_pillars_v382, engine.backtester_v382

### `PROJECTS\four-pillars-backtester\scripts\build_all_specs.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 16:38 | **Lines:** 2190
- **Functions:** check_no_overwrite, ensure_dirs, write_file, gen_backtester_v385, _safe_val, __init__, run, _extract_arrays, col, _snapshot_entry
- **Imports:** os, sys, os, numpy, pandas, typing, engine.backtester_v384, engine.position_v384, numpy, pandas

### `PROJECTS\four-pillars-backtester\scripts\capital_analysis_v383.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 14:06 | **Lines:** 295
- **Functions:** list_5m_coins, load_5m, run_coin, main
- **Imports:** argparse, random, sys, time, numpy, pandas, pathlib, signals.four_pillars_v383, engine.backtester_v383, traceback

### `PROJECTS\four-pillars-backtester\scripts\capital_analysis_v384.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 14:52 | **Lines:** 285
- **Functions:** load_5m, run_coin, main
- **Imports:** argparse, sys, time, numpy, pandas, pathlib, signals.four_pillars_v383, engine.backtester_v384, traceback

### `PROJECTS\four-pillars-backtester\scripts\convert_csv.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 19:36 | **Lines:** 168
- **Functions:** main, _print_format_info, _do_resample
- **Imports:** argparse, json, sys, pathlib, data.normalizer

### `PROJECTS\four-pillars-backtester\scripts\dashboard.py`
- **Why:** recently modified
- **Modified:** 2026-02-12 19:50 | **Lines:** 1498
- **Functions:** get_cached_symbols, resample_5m, load_data, compute_sortino, log_params, run_backtest, compute_params_hash, compute_avg_green_bars
- **Imports:** sys, json, time, hashlib, pathlib, datetime, streamlit, pandas, numpy, plotly.graph_objects

### `PROJECTS\four-pillars-backtester\scripts\dashboard_v2.py`
- **Why:** recently modified
- **Modified:** 2026-02-13 11:10 | **Lines:** 1533
- **Functions:** safe_dataframe, safe_plotly_chart, get_cached_symbols, resample_5m, load_data, compute_sortino, log_params, run_backtest, compute_params_hash, compute_avg_green_bars
- **Imports:** sys, json, time, hashlib, logging, logging.handlers, pathlib, datetime, streamlit, pandas

### `PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 16:36 | **Lines:** 704
- **Functions:** safe_dataframe, safe_plotly_chart, params_hash, load_presets, save_preset, get_cached_symbols, load_cached_data, run_backtest, render_detail_view, render_sidebar
- **Imports:** os, sys, json, time, hashlib, logging, logging.handlers, datetime, streamlit, pandas

### `PROJECTS\four-pillars-backtester\scripts\download_1year_gap_FIXED.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 16:25 | **Lines:** 116
- **Functions:** download_missing_gap, main
- **Imports:** sys, pathlib, datetime, pandas, time, data.fetcher

### `PROJECTS\four-pillars-backtester\scripts\download_all_available.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 10:53 | **Lines:** 485
- **Functions:** backup_cache, load_progress, save_progress, fetch_range, raw_to_df, sanity_check, resample_5m, process_symbol, _export_csv, main
- **Imports:** sys, json, shutil, time, argparse, pathlib, datetime, typing, pandas, data.fetcher

### `PROJECTS\four-pillars-backtester\scripts\download_periods.py`
- **Why:** has __main__, imported by 2 files, recently modified
- **Modified:** 2026-02-13 12:05 | **Lines:** 385
- **Functions:** log, state_file, load_state, save_state, load_listing_dates, save_listing_dates, fetch_range, raw_to_df, sanity_check, process_symbol
- **Imports:** sys, json, time, argparse, pathlib, datetime, pandas, data.fetcher
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\test_download_periods.py, PROJECTS\four-pillars-backtester\scripts\test_download_periods.py

### `PROJECTS\four-pillars-backtester\scripts\download_periods_v2.py`
- **Why:** has __main__, imported by 2 files, recently modified
- **Modified:** 2026-02-13 13:49 | **Lines:** 553
- **Functions:** log, load_coingecko_listing_dates, filter_coins_for_period, state_file, load_state, save_state, load_listing_dates, save_listing_dates, fetch_range, raw_to_df
- **Imports:** sys, json, time, argparse, pathlib, datetime, pandas, data.fetcher
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\test_download_periods_v2.py, PROJECTS\four-pillars-backtester\scripts\test_download_periods_v2.py

### `PROJECTS\four-pillars-backtester\scripts\fetch_coingecko_v2.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 12:35 | **Lines:** 811
- **Functions:** log, progress_bar, eta_str, load_state, save_state, load_env_key, api_get, action_1_coin_history, _save_coin_history, action_2_global_history
- **Imports:** os, sys, json, time, argparse, pathlib, datetime, requests, pandas

### `PROJECTS\four-pillars-backtester\scripts\fetch_market_caps.py`
- **Why:** has __main__, imported by 2 files, recently modified
- **Modified:** 2026-02-13 12:06 | **Lines:** 322
- **Functions:** log, load_env_key, load_state, save_state, fetch_market_chart, main, _save_parquet
- **Imports:** os, sys, json, time, argparse, pathlib, datetime, requests, pandas
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\test_fetch_market_caps.py, PROJECTS\four-pillars-backtester\scripts\test_fetch_market_caps.py

### `PROJECTS\four-pillars-backtester\scripts\lsg_diagnostic_v382.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 12:40 | **Lines:** 305
- **Functions:** list_5m_coins, load_5m, run_coin_trades, analyze_lsg, format_report, main
- **Imports:** argparse, random, sys, time, numpy, pathlib, pandas, signals.four_pillars_v382, engine.backtester_v382

### `PROJECTS\four-pillars-backtester\scripts\mfe_analysis_v383.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 14:10 | **Lines:** 318
- **Functions:** list_5m_coins, load_5m, mfe_to_atr, main
- **Imports:** argparse, random, sys, time, numpy, pandas, pathlib, signals.four_pillars_v383, engine.backtester_v383

### `PROJECTS\four-pillars-backtester\scripts\run_backtest_v382.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 12:41 | **Lines:** 136
- **Functions:** load_cached, list_cached, run_single, print_results, main
- **Imports:** argparse, sys, pathlib, pandas, signals.four_pillars_v382, engine.backtester_v382

### `PROJECTS\four-pillars-backtester\scripts\run_backtest_v383.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 14:33 | **Lines:** 120
- **Functions:** load_cached, print_results, main
- **Imports:** argparse, sys, pathlib, pandas, signals.four_pillars_v383, engine.backtester_v383

### `PROJECTS\four-pillars-backtester\scripts\run_backtest_v384.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 14:55 | **Lines:** 144
- **Functions:** load_cached, print_results, main
- **Imports:** argparse, sys, pathlib, pandas, signals.four_pillars_v383, engine.backtester_v384

### `PROJECTS\four-pillars-backtester\scripts\sanity_check_cache.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 16:25 | **Lines:** 156
- **Functions:** check_file, main
- **Imports:** sys, pathlib, pandas, datetime

### `PROJECTS\four-pillars-backtester\scripts\sweep_sl_mult_v383.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 13:59 | **Lines:** 239
- **Functions:** list_5m_coins, load_5m, run_coin, main
- **Imports:** argparse, random, sys, time, numpy, pathlib, pandas, signals.four_pillars_v383, engine.backtester_v383

### `PROJECTS\four-pillars-backtester\scripts\sweep_tp_v384.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 14:42 | **Lines:** 191
- **Functions:** load_5m, run_config, main, p
- **Imports:** argparse, sys, time, numpy, pandas, pathlib, signals.four_pillars_v383, engine.backtester_v384

### `PROJECTS\four-pillars-backtester\scripts\test_dashboard_v3.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 16:36 | **Lines:** 76
- **Functions:** check, main
- **Imports:** os, sys, importlib.util

### `PROJECTS\four-pillars-backtester\scripts\test_download_periods.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 12:08 | **Lines:** 166
- **Functions:** test, main
- **Imports:** sys, json, tempfile, shutil, pathlib, datetime, pandas, numpy, data.fetcher, download_periods

### `PROJECTS\four-pillars-backtester\scripts\test_download_periods_v2.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 13:47 | **Lines:** 251
- **Functions:** test, main
- **Imports:** sys, json, tempfile, shutil, pathlib, datetime, pandas, numpy, data.fetcher, download_periods_v2

### `PROJECTS\four-pillars-backtester\scripts\test_features_v2.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 12:09 | **Lines:** 235
- **Functions:** test, make_synthetic_ohlcv, make_synthetic_trades, main
- **Imports:** sys, pathlib, datetime, numpy, pandas, ml.features_v2

### `PROJECTS\four-pillars-backtester\scripts\test_fetch_market_caps.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 12:17 | **Lines:** 162
- **Functions:** test, main
- **Imports:** sys, json, tempfile, pathlib, datetime, requests, pandas, fetch_market_caps, fetch_market_caps, shutil

### `PROJECTS\four-pillars-backtester\scripts\test_normalizer.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 20:30 | **Lines:** 637
- **Functions:** check, write_csv, mock_bybit_csv, mock_binance_csv, mock_okx_csv, mock_weex_csv, mock_tradingview_csv, mock_epoch_seconds_csv, mock_5m_csv, mock_tab_csv
- **Imports:** sys, os, tempfile, shutil, pathlib, numpy, pandas, data.normalizer, signals.four_pillars_v383

### `PROJECTS\four-pillars-backtester\scripts\test_period_loader.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 12:10 | **Lines:** 141
- **Functions:** test, main
- **Imports:** sys, pathlib, datetime, pandas, numpy, data.period_loader

### `PROJECTS\four-pillars-backtester\scripts\test_sweep.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 20:02 | **Lines:** 498
- **Functions:** check, _import_dashboard_helpers, compute_params_hash, compute_avg_green_bars, test_params_hash_determinism, test_sweep_csv_write_read, test_sweep_csv_resume, test_sweep_csv_hash_filter, test_avg_green_bars, test_avg_green_bars_short
- **Imports:** sys, os, tempfile, shutil, pathlib, numpy, pandas, importlib, streamlit, hashlib

### `PROJECTS\four-pillars-backtester\scripts\test_v382.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 13:13 | **Lines:** 265
- **Functions:** test_imports, test_avwap, test_position_slot, test_state_machine, test_backtest, main
- **Imports:** sys, pathlib, engine.avwap, engine.position_v382, engine.backtester_v382, signals.state_machine_v382, signals.four_pillars_v382, engine.avwap, engine.position_v382, signals.state_machine_v382

### `PROJECTS\four-pillars-backtester\scripts\test_v383.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 13:59 | **Lines:** 392
- **Functions:** test_imports, test_avwap_clone, test_position_atr_sl, test_position_avwap_sl, test_scale_out, test_state_machine_abcd, test_commission_custom, test_backtest, main
- **Imports:** sys, pathlib, engine.avwap, engine.position_v383, engine.backtester_v383, signals.state_machine_v383, signals.four_pillars_v383, engine.avwap, engine.position_v383, engine.avwap

### `PROJECTS\four-pillars-backtester\scripts\test_v385.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 16:37 | **Lines:** 145
- **Functions:** check, main
- **Imports:** os, sys, numpy, pandas, engine.backtester_v385, signals.four_pillars_v383, engine.backtester_v384

### `PROJECTS\four-pillars-backtester\scripts\test_vince_ml.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 16:36 | **Lines:** 168
- **Functions:** check, main
- **Imports:** os, sys, numpy, pandas, ml.coin_features, torch, ml.vince_model, ml.training_pipeline, tempfile, ml.xgboost_auditor

### `PROJECTS\four-pillars-backtester\scripts\validation_v371_vs_v383.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-12 14:24 | **Lines:** 486
- **Functions:** load_5m, compute_daily_avwap, build_trade_df, stoch_analysis_block, safe_stats, avwap_analysis_block, main, p
- **Imports:** argparse, sys, numpy, pandas, pathlib, signals.four_pillars, signals.four_pillars_v383, engine.backtester, engine.backtester_v383

### `PROJECTS\four-pillars-backtester\signals\four_pillars_v382.py`
- **Why:** imported by 6 files, recently modified
- **Modified:** 2026-02-12 10:49 | **Lines:** 104
- **Functions:** compute_signals_v382
- **Imports:** numpy, pandas, .stochastics, .clouds, .state_machine_v382
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\batch_sweep_v382.py, PROJECTS\four-pillars-backtester\scripts\batch_sweep_v382_be.py, PROJECTS\four-pillars-backtester\scripts\lsg_diagnostic_v382.py, PROJECTS\four-pillars-backtester\scripts\run_backtest_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py

### `PROJECTS\four-pillars-backtester\signals\four_pillars_v383.py`
- **Why:** imported by 18 files, recently modified
- **Modified:** 2026-02-12 13:42 | **Lines:** 111
- **Functions:** compute_signals_v383
- **Imports:** numpy, pandas, .stochastics, .clouds, .state_machine_v383
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\build_all_specs.py, PROJECTS\four-pillars-backtester\scripts\capital_analysis_v383.py, PROJECTS\four-pillars-backtester\scripts\capital_analysis_v384.py, PROJECTS\four-pillars-backtester\scripts\dashboard.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v2.py, PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py, PROJECTS\four-pillars-backtester\scripts\mfe_analysis_v383.py, PROJECTS\four-pillars-backtester\scripts\run_backtest_v383.py, PROJECTS\four-pillars-backtester\scripts\run_backtest_v384.py, PROJECTS\four-pillars-backtester\scripts\sweep_sl_mult_v383.py, PROJECTS\four-pillars-backtester\scripts\sweep_tp_v384.py, PROJECTS\four-pillars-backtester\scripts\test_normalizer.py, PROJECTS\four-pillars-backtester\scripts\test_sweep.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v385.py, PROJECTS\four-pillars-backtester\scripts\validation_v371_vs_v383.py

### `PROJECTS\four-pillars-backtester\signals\state_machine_v382.py`
- **Why:** imported by 3 files, recently modified
- **Modified:** 2026-02-12 13:12 | **Lines:** 240
- **Functions:** any_long, any_short, __init__, process_bar
- **Imports:** dataclasses
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\test_v382.py, PROJECTS\four-pillars-backtester\scripts\test_v382.py, PROJECTS\four-pillars-backtester\signals\four_pillars_v382.py

### `PROJECTS\four-pillars-backtester\signals\state_machine_v383.py`
- **Why:** imported by 3 files, recently modified
- **Modified:** 2026-02-12 13:42 | **Lines:** 339
- **Functions:** any_long, any_short, __init__, process_bar
- **Imports:** dataclasses
- **Imported by:** PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\scripts\test_v383.py, PROJECTS\four-pillars-backtester\signals\four_pillars_v383.py

### `localllm\test_example.py`
- **Why:** recently modified
- **Modified:** 2026-02-13 14:41 | **Lines:** 17
- **Functions:** test_has_title, test_get_started_link
- **Imports:** re, playwright.sync_api

### `vault_sweep.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 15:21 | **Lines:** 532
- **Functions:** find_code_files, extract_imports, extract_functions_classes, build_dependency_map, check_ollama, resolve_model, review_file, write_review_markdown, write_manifest, setup_active_folder
- **Imports:** requests, json, time, argparse, re, os, pathlib, datetime, collections

### `vault_sweep_3.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-13 15:44 | **Lines:** 515
- **Functions:** __init__, start, _tick, update, stop, stop_error, find_code_files, extract_imports, extract_functions_classes, build_dependency_map
- **Imports:** requests, json, time, argparse, re, os, sys, threading, pathlib, datetime

### `vault_sweep_4.py`
- **Why:** has __main__, recently modified
- **Modified:** 2026-02-14 11:08 | **Lines:** 539
- **Functions:** __init__, start, _tick, update, stop, stop_error, find_code_files, extract_imports, extract_functions_classes, build_dependency_map
- **Imports:** requests, json, time, argparse, re, os, sys, threading, pathlib, datetime

---

## Inactive
