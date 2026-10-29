from typing import Any

def summarize_latency_samples(service: str, values_ms: list[float]) -> dict[str, Any]:
    clean: list[float] = []
    for v in values_ms:
        if v is not None and v >= 0:
            clean.append(float(v))
    if not clean:
        return {'service': service, 'count': 0, 'mean': 0.0, 'p95': 0.0, 'status': 'OK'}
    clean.sort()
    mean = round(sum(clean) / len(clean), 2)
    idx = int(round(0.95 * (len(clean) - 1)))
    p95 = round(clean[idx], 2)
    if p95 >= 500.0:
        status = 'CRITICAL'
    elif p95 >= 200.0:
        status = 'WARN'
    else:
        status = 'OK'
    return {'service': service, 'count': len(clean), 'mean': mean, 'p95': p95, 'status': status}

def summarize_error_samples(service: str, rates_pct: list[float]) -> dict[str, Any]:
    clean: list[float] = []
    for v in rates_pct:
        if v is not None and v >= 0:
            clean.append(float(v))
    if not clean:
        return {'service': service, 'count': 0, 'mean': 0.0, 'p95': 0.0, 'status': 'OK'}
    clean.sort()
    mean = round(sum(clean) / len(clean), 2)
    idx = int(round(0.95 * (len(clean) - 1)))
    p95 = round(clean[idx], 2)
    if p95 >= 5.0:
        status = 'CRITICAL'
    elif p95 >= 1.0:
        status = 'WARN'
    else:
        status = 'OK'
    return {'service': service, 'count': len(clean), 'mean': mean, 'p95': p95, 'status': status}

def render_badge(report: dict[str, Any]) -> str:
    return f"[{report['status']}] {report['service']} (n={report['count']}, p95={report['p95']})"
