from typing import Any

def compute_domestic_invoice(items: list[dict[str, Any]], state: str, exempt: bool = False) -> dict[str, Any]:
    sub = 0
    for it in items:
        if it.get('qty', 0) > 0 and it.get('unit_cents', 0) > 0:
            sub += it['qty'] * it['unit_cents']
    disc = int(sub * 0.05) if sub >= 10000 else 0
    taxable = sub - disc
    if exempt:
        rate = 0.0
    elif state == 'CA':
        rate = 0.0825
    elif state == 'NY':
        rate = 0.075
    else:
        rate = 0.06
    tax = int(round(taxable * rate))
    fee = 0 if taxable >= 5000 else 500
    total = taxable + tax + fee
    return {'subtotal': sub, 'discount': disc, 'tax': tax, 'fee': fee, 'total': total, 'region': state}

def compute_export_invoice(items: list[dict[str, Any]], country: str, duty_exempt: bool = False) -> dict[str, Any]:
    sub = 0
    for it in items:
        if it.get('qty', 0) > 0 and it.get('unit_cents', 0) > 0:
            sub += it['qty'] * it['unit_cents']
    disc = int(sub * 0.05) if sub >= 10000 else 0
    taxable = sub - disc
    if duty_exempt:
        rate = 0.0
    elif country == 'DE':
        rate = 0.19
    elif country == 'GB':
        rate = 0.20
    else:
        rate = 0.10
    tax = int(round(taxable * rate))
    fee = 0 if taxable >= 5000 else 500
    total = taxable + tax + fee
    return {'subtotal': sub, 'discount': disc, 'tax': tax, 'fee': fee, 'total': total, 'region': country}

def format_tax_line(summary: dict[str, Any]) -> str:
    return f"{summary['region']}: subtotal={summary['subtotal']} disc={summary['discount']} tax={summary['tax']} fee={summary['fee']} total={summary['total']}"
