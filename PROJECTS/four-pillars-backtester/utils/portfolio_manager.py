"""
Portfolio Manager -- Save, load, list, delete portfolio templates.
Stores coin selections as JSON in portfolios/ directory.
"""
import json
from pathlib import Path
from datetime import datetime


PORTFOLIOS_DIR = Path(__file__).resolve().parent.parent / "portfolios"


def ensure_dir():
    """Create portfolios directory if it does not exist."""
    PORTFOLIOS_DIR.mkdir(parents=True, exist_ok=True)


def save_portfolio(name, coins, selection_method="custom", notes="", params_hash=""):
    """Save a portfolio template to JSON file."""
    ensure_dir()
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in name).strip()
    safe_name = safe_name.replace(" ", "_").lower()
    if not safe_name:
        safe_name = "portfolio_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "name": name,
        "safe_name": safe_name,
        "created": datetime.now().isoformat(),
        "coins": list(coins),
        "coin_count": len(coins),
        "selection_method": selection_method,
        "params_hash": params_hash,
        "notes": notes,
    }
    fpath = PORTFOLIOS_DIR / f"{safe_name}.json"
    fpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(fpath)


def load_portfolio(filename):
    """Load a portfolio template from JSON file. Returns dict or None."""
    fpath = PORTFOLIOS_DIR / filename
    if not fpath.exists():
        return None
    try:
        data = json.loads(fpath.read_text(encoding="utf-8"))
        return data
    except (json.JSONDecodeError, KeyError):
        return None


def list_portfolios():
    """List all saved portfolios. Returns list of dicts with name, file, coin_count, created."""
    ensure_dir()
    result = []
    for f in sorted(PORTFOLIOS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "file": f.name,
                "name": data.get("name", f.stem),
                "coin_count": data.get("coin_count", len(data.get("coins", []))),
                "created": data.get("created", ""),
                "selection_method": data.get("selection_method", ""),
                "notes": data.get("notes", ""),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return result


def delete_portfolio(filename):
    """Delete a portfolio template file. Returns True if deleted."""
    fpath = PORTFOLIOS_DIR / filename
    if fpath.exists():
        fpath.unlink()
        return True
    return False


def rename_portfolio(old_filename, new_name):
    """Rename a portfolio (updates name field and filename)."""
    data = load_portfolio(old_filename)
    if data is None:
        return None
    delete_portfolio(old_filename)
    return save_portfolio(
        name=new_name,
        coins=data["coins"],
        selection_method=data.get("selection_method", "custom"),
        notes=data.get("notes", ""),
        params_hash=data.get("params_hash", ""),
    )
