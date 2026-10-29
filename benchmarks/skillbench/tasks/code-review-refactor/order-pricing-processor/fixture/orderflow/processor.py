"""Order pricing, discount, shipping, tax, and receipt calculation."""

from __future__ import annotations

from typing import Any


def process_order(d: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(d, dict):
        raise ValueError("order must be a dict")
    if "customer" not in d or not str(d["customer"]).strip():
        raise ValueError("customer is required")
    if "items" not in d or not isinstance(d["items"], list) or len(d["items"]) == 0:
        raise ValueError("items must be a non-empty list")
    r = d.get("region", "US-CA")
    if r not in ("US-CA", "US-NY", "US-OR", "CA", "EU"):
        raise ValueError(f"unsupported region: {r}")

    lines: list[dict[str, Any]] = []
    sub = 0
    for it in d["items"]:
        if not isinstance(it, dict):
            raise ValueError("each item must be a dict")
        nm = str(it.get("name", "")).strip()
        q = it.get("qty", 0)
        p = it.get("unit_cents", -1)
        if not nm:
            raise ValueError("item name is required")
        if not isinstance(q, int) or q <= 0:
            raise ValueError("item qty must be a positive int")
        if not isinstance(p, int) or p < 0:
            raise ValueError("item unit_cents must be a non-negative int")
        if q >= 50:
            u = (p * 85) // 100
        else:
            if q >= 20:
                u = (p * 90) // 100
            else:
                if q >= 10:
                    u = (p * 95) // 100
                else:
                    u = p
        lt = u * q
        sub += lt
        lines.append({"name": nm, "qty": q, "unit_cents": u, "line_cents": lt})

    c = str(d.get("coupon") or "").strip().upper()
    disc = 0
    if c:
        if c == "SAVE10":
            disc = (sub * 10) // 100
        else:
            if c == "VIP20":
                disc = (sub * 20) // 100
            else:
                if c == "FLAT500":
                    disc = 500 if sub >= 500 else sub
                else:
                    raise ValueError(f"unknown coupon: {c}")

    after_disc = sub - disc
    if r in ("US-CA", "US-NY", "US-OR"):
        if after_disc >= 10000:
            sh = 0
        else:
            sh = 799
    else:
        if r == "CA":
            if after_disc >= 15000:
                sh = 0
            else:
                sh = 1299
        else:
            if after_disc >= 20000:
                sh = 0
            else:
                sh = 1999

    if r == "US-CA":
        tx = (after_disc * 825) // 10000
    else:
        if r == "US-NY":
            tx = (after_disc * 800) // 10000
        else:
            if r == "US-OR":
                tx = 0
            else:
                if r == "CA":
                    tx = (after_disc * 1300) // 10000
                else:
                    tx = (after_disc * 2000) // 10000

    tot = after_disc + sh + tx
    return {
        "customer": str(d["customer"]).strip(),
        "region": r,
        "status": "CONFIRMED",
        "lines": lines,
        "subtotal_cents": sub,
        "discount_cents": disc,
        "shipping_cents": sh,
        "tax_cents": tx,
        "total_cents": tot,
    }


def estimate_order(d: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(d, dict):
        raise ValueError("order must be a dict")
    if "customer" not in d or not str(d["customer"]).strip():
        raise ValueError("customer is required")
    if "items" not in d or not isinstance(d["items"], list) or len(d["items"]) == 0:
        raise ValueError("items must be a non-empty list")
    r = d.get("region", "US-CA")
    if r not in ("US-CA", "US-NY", "US-OR", "CA", "EU"):
        raise ValueError(f"unsupported region: {r}")

    sub = 0
    for it in d["items"]:
        if not isinstance(it, dict):
            raise ValueError("each item must be a dict")
        nm = str(it.get("name", "")).strip()
        q = it.get("qty", 0)
        p = it.get("unit_cents", -1)
        if not nm:
            raise ValueError("item name is required")
        if not isinstance(q, int) or q <= 0:
            raise ValueError("item qty must be a positive int")
        if not isinstance(p, int) or p < 0:
            raise ValueError("item unit_cents must be a non-negative int")
        if q >= 50:
            u = (p * 85) // 100
        else:
            if q >= 20:
                u = (p * 90) // 100
            else:
                if q >= 10:
                    u = (p * 95) // 100
                else:
                    u = p
        sub += u * q

    c = str(d.get("coupon") or "").strip().upper()
    disc = 0
    if c:
        if c == "SAVE10":
            disc = (sub * 10) // 100
        else:
            if c == "VIP20":
                disc = (sub * 20) // 100
            else:
                if c == "FLAT500":
                    disc = 500 if sub >= 500 else sub
                else:
                    raise ValueError(f"unknown coupon: {c}")

    after_disc = sub - disc
    if r in ("US-CA", "US-NY", "US-OR"):
        if after_disc >= 10000:
            sh = 0
        else:
            sh = 799
    else:
        if r == "CA":
            if after_disc >= 15000:
                sh = 0
            else:
                sh = 1299
        else:
            if after_disc >= 20000:
                sh = 0
            else:
                sh = 1999

    if r == "US-CA":
        tx = (after_disc * 825) // 10000
    else:
        if r == "US-NY":
            tx = (after_disc * 800) // 10000
        else:
            if r == "US-OR":
                tx = 0
            else:
                if r == "CA":
                    tx = (after_disc * 1300) // 10000
                else:
                    tx = (after_disc * 2000) // 10000

    return {
        "subtotal_cents": sub,
        "discount_cents": disc,
        "shipping_cents": sh,
        "tax_cents": tx,
        "total_cents": after_disc + sh + tx,
    }


def format_receipt(res: dict[str, Any]) -> str:
    out = [f"Receipt for {res['customer']} ({res['region']})"]
    for ln in res["lines"]:
        out.append(f"- {ln['name']} x{ln['qty']}: {ln['line_cents']}c")
    out.append(f"Subtotal: {res['subtotal_cents']}c")
    out.append(f"Discount: -{res['discount_cents']}c")
    out.append(f"Shipping: {res['shipping_cents']}c")
    out.append(f"Tax: {res['tax_cents']}c")
    out.append(f"Total: {res['total_cents']}c")
    return "\n".join(out)
