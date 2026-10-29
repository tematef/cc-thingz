"""Structured log line analyzer and alert classifier."""

from __future__ import annotations

from typing import Any


def analyze_log_lines(lines: list[str]) -> dict[str, Any]:
    svc_map: dict[str, dict[str, Any]] = {}
    bad = 0
    tot = 0

    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) < 2:
            bad += 1
            continue
        ts = parts[0]
        kv: dict[str, str] = {}
        ok_line = True
        for tok in parts[1:]:
            if "=" not in tok:
                ok_line = False
                break
            k, v = tok.split("=", 1)
            kv[k.strip()] = v.strip()
        if not ok_line or "service" not in kv or "level" not in kv:
            bad += 1
            continue
        lvl = kv["level"].upper()
        if lvl == "WARN":
            lvl = "WARNING"
        elif lvl == "ERR":
            lvl = "ERROR"
        elif lvl == "CRIT":
            lvl = "CRITICAL"
        if lvl not in ("INFO", "WARNING", "ERROR", "CRITICAL"):
            bad += 1
            continue
        try:
            lat = int(kv.get("latency_ms", "0"))
            st_code = int(kv.get("status", "200"))
        except ValueError:
            bad += 1
            continue
        if lat < 0 or st_code < 100 or st_code > 599:
            bad += 1
            continue

        tot += 1
        sn = kv["service"]
        if sn not in svc_map:
            svc_map[sn] = {
                "count": 0,
                "err": 0,
                "s5xx": 0,
                "lat_sum": 0,
                "lat_max": 0,
                "last_ts": ts,
            }
        b = svc_map[sn]
        b["count"] += 1
        if lvl in ("ERROR", "CRITICAL") or st_code >= 500:
            b["err"] += 1
        if st_code >= 500:
            b["s5xx"] += 1
        b["lat_sum"] += lat
        if lat > b["lat_max"]:
            b["lat_max"] = lat
        b["last_ts"] = ts

    out_svcs: dict[str, dict[str, Any]] = {}
    for sn in sorted(svc_map):
        b = svc_map[sn]
        c = b["count"]
        er = round(b["err"] / c, 4) if c > 0 else 0.0
        avg_l = b["lat_sum"] // c if c > 0 else 0
        if er >= 0.20 or b["s5xx"] >= 3:
            hlth = "critical"
        else:
            if er >= 0.05 or b["lat_max"] >= 1000:
                hlth = "warning"
            else:
                hlth = "healthy"
        out_svcs[sn] = {
            "total_events": c,
            "error_events": b["err"],
            "http_5xx_count": b["s5xx"],
            "error_rate": er,
            "avg_latency_ms": avg_l,
            "max_latency_ms": b["lat_max"],
            "health": hlth,
            "last_timestamp": b["last_ts"],
        }

    return {
        "valid_events": tot,
        "malformed_lines": bad,
        "services": out_svcs,
    }


def filter_critical_events(lines: list[str]) -> list[dict[str, Any]]:
    res: list[dict[str, Any]] = []
    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) < 2:
            continue
        ts = parts[0]
        kv: dict[str, str] = {}
        ok_line = True
        for tok in parts[1:]:
            if "=" not in tok:
                ok_line = False
                break
            k, v = tok.split("=", 1)
            kv[k.strip()] = v.strip()
        if not ok_line or "service" not in kv or "level" not in kv:
            continue
        lvl = kv["level"].upper()
        if lvl == "WARN":
            lvl = "WARNING"
        elif lvl == "ERR":
            lvl = "ERROR"
        elif lvl == "CRIT":
            lvl = "CRITICAL"
        if lvl not in ("INFO", "WARNING", "ERROR", "CRITICAL"):
            continue
        try:
            lat = int(kv.get("latency_ms", "0"))
            st_code = int(kv.get("status", "200"))
        except ValueError:
            continue
        if lat < 0 or st_code < 100 or st_code > 599:
            continue
        if lvl == "CRITICAL" or st_code >= 500 or lat >= 1000:
            res.append(
                {
                    "timestamp": ts,
                    "service": kv["service"],
                    "level": lvl,
                    "status": st_code,
                    "latency_ms": lat,
                    "msg": kv.get("msg", ""),
                }
            )
    return res


def render_markdown_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Service Log Summary",
        f"Valid events: {report['valid_events']} | Malformed: {report['malformed_lines']}",
    ]
    for name, info in report["services"].items():
        lines.append(
            f"- {name}: {info['health'].upper()} "
            f"(events={info['total_events']}, errors={info['error_events']}, "
            f"max_latency={info['max_latency_ms']}ms)"
        )
    return "\n".join(lines)
