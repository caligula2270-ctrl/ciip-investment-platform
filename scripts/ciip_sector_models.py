"""Conservative *sector-specific* research valuations from SEC-reported annual facts.

Three deliberately separate methodologies:
- Software: owner cash proxy after subtracting SBC *as a stress*, no implied
  claim that subtracting SBC and forecasting dilution together is appropriate.
- Payment networks: income-capped FCF; aggregate illustrative value ONLY until
  settlement and exchangeable share classes are reconciled with capital notes.
- Capital-heavy operations: 5Y presence, replacement/expansion proxy uses full
  CAPEX and stresses it upward; D&A is never a maintenance-CAPEX substitute.

No valuation here is a fair-price recommendation or a verified current share
price. No market prices are necessary for computing model amounts.
"""
from __future__ import annotations

import math
import statistics

from ciip_quality_controls import sector_control

SOFTWARE = {"software"}
PAYMENTS = {"payment_network"}
CAPITAL = {"capital_intensive", "cyclical_semis", "cloud_capex"}


def med(items):
    v = [float(x) for x in items if isinstance(x, (float, int)) and math.isfinite(x)]
    return statistics.median(v) if v else None


def gaap(row, field):
    obj = row.get("metrics", {}).get(field)
    return obj.get("value") if isinstance(obj, dict) else None


def dcf_flow(cash_usd, first_growth, later_growth, discount, terminal, years=10):
    if not (isinstance(cash_usd, (int, float)) and math.isfinite(cash_usd) and cash_usd > 0):
        return None
    if not (0 < discount < .40 and -.05 <= terminal <= .05 and discount > terminal + .005):
        return None
    f = float(cash_usd)
    pv = 0.
    for year in range(1, years + 1):
        f *= 1 + (first_growth if year <= years // 2 else later_growth)
        pv += f / (1 + discount)**year
    tv = f * (1 + terminal) / (discount - terminal)
    terminal_pv = tv / (1 + discount)**years
    total = pv + terminal_pv
    if not math.isfinite(total) or total <= 0:
        return None
    return {"equity_value_usd": round(total, 2),
            "terminal_weight_pct": round(100 * terminal_pv / total, 2),
            "explicit_value_usd": round(pv, 2),
            "terminal_value_pv_usd": round(terminal_pv, 2)}


def build_sector_valuation(ticker, rows, quality, shares=None, capital_notes=None):
    sector = sector_control(ticker)
    p = sector["profile"]
    model = "standard_dcf"
    if p in SOFTWARE: model = "software_owner_cash_sbc_stress"
    elif p in PAYMENTS: model = "payments_income_capped_cashflow"
    elif p in CAPITAL: model = "capital_heavy_peak_capex_stress"
    result = {
        "schema": "ciip-sector-valuation-v1",
        "sector": p, "model": model,
        "status": "not_applicable", "source": "SEC 10-K, CFO, CAPEX and US GAAP concepts",
        "methodology": "Research-only; not a price target or audited FCFE.",
        "normalized_cash_usd": None,
        "adjustments": {}, "scenarios": {}, "warnings": [],
        "shares_review": shares.get("status") if shares else "unavailable",
        "capital_notes_status": (capital_notes or {}).get("status", "not_reviewed"),
    }
    if model == "standard_dcf": return result
    if not rows or len(rows) < 3:
        result["status"] = "insufficient"
        result["warnings"].append("Menos de tres ejercicios SEC con historial")
        return result
    recent = rows[-3:]
    if quality.get("latest_fy_age_days") is None or quality["latest_fy_age_days"] > 520:
        result["status"] = "insufficient"
        result["warnings"].append("Último 10-K demasiado antiguo")
        return result
    cfo = [gaap(x, "operating_cash_flow") for x in recent]
    capex = [gaap(x, "capex") for x in recent]
    fcf = [x.get("fcf_usd") for x in recent]
    if any(v is None or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in cfo + capex + fcf) or any(v < 0 for v in capex):
        result["status"] = "insufficient"
        result["warnings"].append("Falta CFO, CAPEX o FCF comparable en tres ejercicios")
        return result
    if any(v <= 0 for v in fcf):
        result["status"] = "insufficient"
        result["warnings"].append("FCF no positivo en alguno de los tres ejercicios")
        return result

    normal = quality.get("normalized_fcf_3y_usd")
    if not isinstance(normal, (int, float)) or normal <= 0:
        # Payment-network branch can work even when the generic industrial DCF
        # is blocked by the *sector*, but NOT if the underlying data are missing
        # or material working-capital movements triggered a block.
        if model != "payments_income_capped_cashflow" or quality.get("normalized_fcf_status") == "working_capital_review":
            result["status"] = "insufficient"
            result["warnings"].append("No supera la normalización contable o el control del circulante")
            return result
        median_fcf = med(fcf)
        med_cfo, med_cap = med(cfo), med(capex)
        normal = min(median_fcf, med_cfo - med_cap)
    if normal <= 0:
        result["status"] = "insufficient"
        result["warnings"].append("Base normalizada no positiva")
        return result

    base = normal
    revenue_growth = quality.get("revenue_cagr_pct")
    if revenue_growth is None or not math.isfinite(revenue_growth):
        result["status"] = "insufficient"
        result["warnings"].append("CAGR de ingresos no disponible para calibrar escenario")
        return result
    g = max(-.02, min(.15, revenue_growth / 100.0))
    if model == "software_owner_cash_sbc_stress":
        sbc = [gaap(r, "stock_compensation") for r in recent]
        if any(v is None or v < 0 for v in sbc):
            result["status"] = "insufficient"
            result["warnings"].append("SBC no disponible en los tres 10-K; no estimar económicamente dilución")
            return result
        sbc_median = med(sbc)
        base = normal - sbc_median
        result["adjustments"] = {
            "fcf_3y_usd": normal, "median_sbc_3y_usd": sbc_median,
            "owner_cash_proxy_usd": base,
            "sbc_policy": "100% median GAAP stock compensation subtracted as economic-cost stress; do not extrapolate share dilution as an additional charge",
        }
        assumptions = {"first_growth": min(.09, max(0, g * .65)),
                       "later_growth": min(.045, max(0, g * .40)),
                       "discount_rate": .115, "terminal_growth": .02}
        result["warnings"].append("SBC se resta como estrés económico; puede coexistir con dilución y exige evitar doble contabilización")
        result["warnings"].append("R&D, ingresos diferidos, capitalización de software y recompras pendientes de análisis")
    elif model == "payments_income_capped_cashflow":
        earnings = [gaap(r, "net_income") for r in recent]
        if any(v is None or v <= 0 for v in earnings):
            result["status"] = "insufficient"
            result["warnings"].append("Faltan tres ejercicios de beneficio neto positivo")
            return result
        net_median = med(earnings)
        # A conservative cap, NOT a claim of 95% cash conversion.
        base = min(normal, .95 * net_median)
        result["adjustments"] = {
            "fcf_3y_usd": normal, "net_income_median_3y_usd": net_median,
            "income_haircut_pct": 5, "cash_cap_usd": .95 * net_median,
            "owner_cash_proxy_usd": base,
        }
        assumptions = {"first_growth": min(.075, max(0, g * .55)),
                       "later_growth": min(.04, max(0, g * .30)),
                       "discount_rate": .12, "terminal_growth": .02}
        result["warnings"].append("Las liquidaciones con participantes y reservas regulatorias no están normalizadas con XBRL consolidado")
        result["warnings"].append("Valores patrimoniales SOLO indicativos: acciones clase B/C, conversiones y notas de capital requieren verificación manual")
        result["warnings"].append("No emitir señal de compra ni valoración por acción automática para redes de pagos")
    else:
        if len(rows) < 5:
            result["status"] = "insufficient"
            result["warnings"].append("Negocio intensivo: se necesitan cinco ejercicios SEC para incluir el ciclo")
            return result
        med_capex = med(capex)
        high_capex = max(capex)
        baseline_cfo = med(cfo)
        # Stress using the highest real CAPEX year, not accounting depreciation.
        stressed = baseline_cfo - high_capex
        base = min(normal, stressed)
        result["adjustments"] = {
            "fcf_3y_usd": normal, "median_cfo_3y_usd": baseline_cfo,
            "median_capex_3y_usd": med_capex, "peak_capex_3y_usd": high_capex,
            "peak_capex_stress_cash_usd": stressed, "owner_cash_proxy_usd": base,
        }
        assumptions = {"first_growth": min(.055, max(-.01, g * .45)),
                       "later_growth": min(.025, max(0, g * .20)),
                       "discount_rate": .13, "terminal_growth": .015}
        result["warnings"].append("CAPEX máximo trianual se usa como estrés; no es mantenimiento certificado ni normalización de un ciclo completo")
        if p in {"cyclical_semis", "cloud_capex"}:
            result["warnings"].append("Riesgo de ciclo/fase de inversión; el crecimiento e infraestructura deben modelarse por segmentos")
    if base <= 0:
        result["status"] = "insufficient"
        result["warnings"].append("El flujo prudente del modelo sectorial es nulo o negativo")
        return result
    result["normalized_cash_usd"] = round(base, 2)
    result["assumptions"] = {k: round(v * 100, 3) for k, v in assumptions.items()}
    # Lower/higher required-return variants: no claiming target prices.
    for name, gmult, rup in (("conservador", .5, .025), ("base", 1, 0), ("optimista", 1.25, -.01)):
        growth1 = assumptions["first_growth"] * gmult
        growth2 = assumptions["later_growth"] * gmult
        discount = assumptions["discount_rate"] + rup
        d = dcf_flow(base, growth1, growth2, discount, assumptions["terminal_growth"])
        if d: result["scenarios"][name] = {
            **d, "growth_1_5_pct": round(growth1 * 100, 2),
            "growth_6_10_pct": round(growth2 * 100, 2),
            "discount_pct": round(discount * 100, 2),
            "terminal_pct": assumptions["terminal_growth"] * 100,
        }
    if not result["scenarios"]:
        result["status"] = "insufficient"
        return result
    if model == "payments_income_capped_cashflow":
        result["status"] = "aggregate_research_only"
    else:
        result["status"] = "review_required"
    if quality.get("normalized_fcf_status") == "working_capital_review":
        result["status"] = "insufficient"
        result["normalized_cash_usd"] = None
        result["scenarios"] = {}
        result["warnings"].append("Bloqueado: sensibilidad material del circulante")
    return result
