"""Quality controls for CIIP SEC fundamentals: cautious and source-linked.

Never interpret depreciation as true maintenance CAPEX, or partial working
capital movements as a complete cash-flow adjustment. Current SEC share
counts are basic/cover-page counts, not diluted shares.
"""
from __future__ import annotations

import datetime as dt
import math
import statistics

# Explicit classifications for the CIIP US issuer universe.
# This is an analytical policy list, not an SEC industry classification.
SECTORS = {
    "MSFT": ("cloud_capex", "Nube / centros de datos", "review"),
    "GOOGL": ("cloud_capex", "Publicidad / nube / centros de datos", "review"),
    "AMZN": ("mixed_operations", "Retail, nube y logística", "blocked"),
    "META": ("cloud_capex", "Publicidad y centros de datos", "review"),
    "V": ("payment_network", "Red de pagos", "blocked"),
    "MA": ("payment_network", "Red de pagos", "blocked"),
    "SPGI": ("financial_data", "Ratings, índices y datos", "review"),
    "MCO": ("financial_data", "Ratings y analítica", "review"),
    "COST": ("retail", "Distribución e inventarios", "review"),
    "CPRT": ("standard", "Subastas y servicios", "eligible"),
    "FICO": ("software", "Software y modelos de puntuación", "eligible"),
    "ROP": ("serial_acquirer", "Compras recurrentes de empresas", "review"),
    "HEI": ("serial_acquirer", "Componentes aeroespaciales y adquisiciones", "review"),
    "TDG": ("serial_acquirer", "Componentes aeroespaciales y adquisiciones", "review"),
    "INTU": ("software", "Software financiero", "eligible"),
    "ADBE": ("software", "Software creativo", "eligible"),
    "TXN": ("cyclical_semis", "Fabricación de semiconductores", "review"),
    "LRCX": ("cyclical_semis", "Equipos de semiconductores", "review"),
    "BKNG": ("travel_platform", "Plataforma turística con cobros por cuenta de terceros", "review"),
    "MELI": ("mixed_operations", "Comercio / crédito / pagos", "blocked"),
    "AZO": ("retail", "Distribución con inventarios", "review"),
    "ORLY": ("retail", "Distribución con inventarios", "review"),
    "ODFL": ("capital_intensive", "Transporte con flota e infraestructura", "review"),
    "VRSK": ("software", "Datos y analítica de seguros, no aseguradora", "eligible"),
    "AON": ("insurance_broker", "Correduría de seguros y cuentas fiduciarias", "review"),
    "DHR": ("serial_acquirer", "Ciencias de la vida y adquisiciones", "review"),
    "MEDP": ("contract_research", "Investigación clínica por contrato", "review"),
    "OXY": ("energy", "Petróleo, gas y reservas", "blocked"),
    "AAON": ("capital_intensive", "Fabricación de climatización", "review"),
    "TRUP": ("insurer", "Aseguradora de mascotas", "blocked"),
    "TBBB": ("foreign_special", "Emisor extranjero / retail; obligaciones sectoriales", "blocked"),
    "FRPH": ("real_estate", "Inmuebles y terrenos; requiere NAV / NOI", "blocked"),
}
MULTICLASS = {"GOOGL", "META", "V", "MA", "HEI", "TBBB"}
HIST_EXTRA = {
    "depreciation": ["DepreciationDepletionAndAmortization", "DepreciationDepletionAndAmortizationPropertyPlantAndEquipment"],
    "stock_compensation": ["ShareBasedCompensation"],
    "receivables": ["AccountsReceivableNetCurrent"],
    "inventory": ["InventoryNet"],
    "payables": ["AccountsPayableCurrent"],
    "acquisitions": ["PaymentsToAcquireBusinessesNetOfCashAcquired"],
}
INSTANTS = {"receivables", "inventory", "payables"}
CURRENT_SHARES = (
    ("dei", "EntityCommonStockSharesOutstanding"),
    ("us-gaap", "CommonStockSharesOutstanding"),
)
QUARTERLY_DILUTED = ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding")


def sector_control(ticker):
    profile, description, status = SECTORS.get(ticker, ("unclassified", "Sector no clasificado", "blocked"))
    notes = {
        "cloud_capex": "CAPEX de crecimiento y mantenimiento no identificable con certeza; DCF sujeto a revisión.",
        "payment_network": "Revisar liquidaciones, derechos económicos de clases y red de pagos; DCF genérico bloqueado.",
        "retail": "Revisar financiación por proveedores, inventarios y capital circulante estacional.",
        "serial_acquirer": "Adquisiciones recurrentes excluidas de CFO-CAPEX; ajustar reinversión económica.",
        "cyclical_semis": "Ciclo y normalización de capacidad: un FCF de tres años puede no cubrir un ciclo completo.",
        "energy": "Se requiere análisis de reservas, declino, reinversión y precios de materias primas.",
        "insurer": "El modelo de flujos industriales no sirve para reservas, primas ni capital regulatorio.",
        "real_estate": "Se requiere NOI, cap rate, NAV y deuda por activo, no CFO-CAPEX genérico.",
        "mixed_operations": "Flujos mezclados de líneas con capital intensivo / servicios financieros: desagregar.",
        "financial_data": "Examinar capital regulatorio / riesgos de emisión y efectos de cartera antes de comparar.",
        "foreign_special": "Revisar estructura de capital, informes por jurisdicción y contabilidad comparable.",
        "insurance_broker": "Revisar saldos en nombre de clientes y remuneraciones; CFO puede contener efectivo fiduciario.",
        "travel_platform": "Verificar cobros por cuenta de terceros y cambios de capital circulante.",
        "contract_research": "Los anticipos de clientes pueden elevar CFO de forma no recurrente.",
        "capital_intensive": "Normalizar CAPEX de reposición/ciclo; amortización no sustituye a CAPEX.",
        "software": "Revisar compensación basada en acciones, capitalización de desarrollo y dilución.",
        "standard": "Aun en negocios operativos convencionales, revisar CAPEX y flujo de circulante.",
        "unclassified": "Sin clasificación sectorial validada; valoración bloqueada.",
    }
    return {"profile": profile, "description": description, "status": status, "reason": notes[profile]}


def _select_annual(facts, year, tags, unit="USD", instant=False, as_of=None):
    candidates = []
    for priority, tag in enumerate(tags):
        for x in facts.get("us-gaap", {}).get(tag, {}).get("units", {}).get(unit, []):
            try:
                if x.get("form") not in ("10-K", "10-K/A") or not x.get("accn"): continue
                end = dt.date.fromisoformat(x["end"])
                filed = dt.date.fromisoformat(x["filed"])
                if end.isoformat() != year or (as_of and filed > as_of): continue
                start = dt.date.fromisoformat(x["start"]) if x.get("start") else None
                if instant:
                    if start is not None: continue
                elif start is None or not 330 <= (end - start).days <= 390:
                    continue
                val = x.get("val")
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val): continue
                candidates.append((filed, -priority, {
                    "value": val, "end": x["end"], "start": x.get("start"),
                    "filed": x["filed"], "form": x["form"],
                    "accession": x["accn"], "tag": tag,
                    "unit": unit, "taxonomy": "us-gaap",
                    "period": "instant" if instant else "FY",
                }))
            except (ValueError, TypeError, KeyError, OverflowError):
                continue
    return max(candidates, key=lambda x: (x[0], x[1]))[2] if candidates else None


def _median(values):
    ok = [v for v in values if v is not None and isinstance(v, (int, float)) and math.isfinite(v)]
    return statistics.median(ok) if ok else None


def _numeric_metric(row, name):
    x = row.get("metrics", {}).get(name)
    return x["value"] if x is not None else None


def quality_normalize(facts, rows, quality, ticker, as_of):
    """Annotate 5Y fiscal rows and build a deliberately conservative 3Y baseline."""
    profile = sector_control(ticker)
    for row in rows:
        for field, tags in HIST_EXTRA.items():
            x = _select_annual(facts, row["fy_end"], tags,
                               instant=field in INSTANTS, as_of=as_of)
            if x:
                row["metrics"][field] = x
        receivables = _numeric_metric(row, "receivables")
        inventory = _numeric_metric(row, "inventory")
        payables = _numeric_metric(row, "payables")
        # Complete PARTIAL working capital balance; not overall NWC.
        row["partial_operating_wc_usd"] = (
            receivables + inventory - payables
            if all(x is not None for x in (receivables, inventory, payables))
            else None
        )
        capex, dep = _numeric_metric(row, "capex"), _numeric_metric(row, "depreciation")
        row["capex_to_depreciation_ratio"] = (
            capex / dep if capex is not None and dep is not None and dep > 0 else None
        )
        # The conservative reported FCF includes ALL CAPEX, no artificial
        # "growth CAPEX" addback. Depreciation is diagnostic only.
        row["maintenance_capex_proxy_usd"] = (
            min(capex, dep) if capex is not None and capex >= 0 and
            dep is not None and dep >= 0 else None
        )
    previous = None
    for row in rows:
        curr = row["partial_operating_wc_usd"]
        row["partial_wc_cash_impact_usd"] = (
            -(curr - previous) if curr is not None and previous is not None else None
        )
        previous = curr
    last3 = rows[-3:]
    cfo = [_numeric_metric(y, "operating_cash_flow") for y in last3]
    capex = [_numeric_metric(y, "capex") for y in last3]
    reported = [y.get("fcf_usd") for y in last3]
    valid3 = len(last3) == 3 and all(
        x is not None and math.isfinite(x) for x in cfo + capex + reported
    ) and all(x > 0 for x in reported) and all(x >= 0 for x in capex)
    median_cfo = _median(cfo) if valid3 else None
    median_capex = _median(capex) if valid3 else None
    median_fcf = _median(reported) if valid3 else None
    separate = median_cfo - median_capex if valid3 else None
    # Use lower of median annual FCF and separately normalized CFO-CAPEX.
    # This discourages a one-off low CAPEX year from inflating value.
    baseline = min(median_fcf, separate) if valid3 and separate > 0 else None
    note = []
    if median_capex is None:
        note.append("Sin tres ejercicios completos de CFO y CAPEX para normalizar reinversión")
    if median_capex is not None and median_cfo and median_cfo > 0:
        share = median_capex / median_cfo
        if share > 0.70:
            note.append("CAPEX mediano >70 % de CFO: reinversión intensiva")
    capex_positive = [v for v in capex if v is not None and v > 0]
    if len(capex_positive) == 3 and max(capex_positive) / min(capex_positive) > 2.5:
        note.append("CAPEX muy variable (máximo/mínimo >2,5×)")
    impacts = [r["partial_wc_cash_impact_usd"] for r in last3 if r["partial_wc_cash_impact_usd"] is not None]
    max_impact = max((abs(v) for v in impacts), default=None)
    wc_material = bool(max_impact is not None and median_cfo and median_cfo > 0 and
                       max_impact / median_cfo > 0.35)
    if wc_material:
        note.append("Movimiento de circulante parcial >35 % del CFO mediano: normalización requiere revisión")
    elif not impacts:
        note.append("Sin datos suficientes para conciliar cuentas a cobrar, existencias y proveedores")
    else:
        note.append("Circulante calculado parcialmente (AR + inventario − proveedores); no representa todos los ajustes CFO")
    sbcs = [_numeric_metric(y, "stock_compensation") for y in last3]
    sbc_med = _median(sbcs) if len(last3) == 3 and all(x is not None for x in sbcs) else None
    if sbc_med is not None and median_cfo is not None and median_cfo > 0 and sbc_med / median_cfo > 0.20:
        note.append("Compensación en acciones >20 % CFO; revisar dilución y coste económico")
    if profile["status"] == "blocked":
        note.append("DCF genérico bloqueado por controles sectoriales")
    elif profile["status"] == "review":
        note.append("Se exige validación sectorial adicional antes de utilizar DCF como precio objetivo")
    quality["reported_fcf_median_3y_usd"] = median_fcf
    quality["median_cfo_3y_usd"] = median_cfo
    quality["median_capex_3y_usd"] = median_capex
    quality["separate_medians_fcf_3y_usd"] = separate
    quality["normalized_fcf_3y_usd"] = (
        baseline if baseline is not None and baseline > 0 and quality.get("latest_fy_age_days") is not None
        and quality["latest_fy_age_days"] <= 520 and not wc_material
        and profile["status"] != "blocked" else None
    )
    quality["normalized_fcf_status"] = (
        "sector_blocked" if profile["status"] == "blocked" else
        "working_capital_review" if wc_material else
        "ready_with_caveats" if quality["normalized_fcf_3y_usd"] else "insufficient"
    )
    quality["partial_wc_largest_annual_cash_effect_usd"] = max_impact
    quality["partial_wc_has_complete_3y"] = len(impacts) >= 2
    quality["median_sbc_3y_usd"] = sbc_med
    quality["sector_profile"] = profile["profile"]
    quality["normalization_notes"] = note
    # Legacy flag names retained, yet only the stricter new field may drive DCF.
    return profile


def _shares_candidates(facts, taxonomy, tag, as_of):
    observations = facts.get(taxonomy, {}).get(tag, {}).get("units", {}).get("shares", [])
    rows = []
    for x in observations:
        try:
            if x.get("form") not in ("10-Q", "10-K", "10-K/A", "10-Q/A"): continue
            filed = dt.date.fromisoformat(x["filed"])
            end = dt.date.fromisoformat(x["end"])
            if filed > as_of or end > as_of or (as_of - end).days > 540: continue
            val = x.get("val")
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not 1e5 <= val <= 1e12:continue
            if not math.isfinite(val):continue
            start = dt.date.fromisoformat(x["start"]) if x.get("start") else None
            if tag == QUARTERLY_DILUTED[1]:
                if start is None or not 70 <= (end - start).days <= 110: continue
            elif start is not None:continue
            if not x.get("accn"): continue
            rows.append({
                "value": int(val), "end": end.isoformat(), "filed": filed.isoformat(),
                "form": x["form"], "accession": x["accn"], "tag": tag,
                "taxonomy": taxonomy, "unit": "shares",
            })
        except (ValueError, KeyError, TypeError, OverflowError):
            continue
    rows.sort(key=lambda z: (z["end"], z["filed"]), reverse=True)
    return rows


def current_share_reconciliation(facts, ticker, quality, as_of):
    """Compare SEC cover/basic vs recent quarterly diluted with strict vetoes.

    SEC companyfacts exclude dimensional class facts: a company with several
    share classes must be reconciled manually, even if a number is present.
    """
    candidates = [_shares_candidates(facts, ns, tag, as_of) for ns, tag in CURRENT_SHARES]
    cover, basic = (x[0] if x else None for x in candidates)
    quarter_rows = _shares_candidates(facts, *QUARTERLY_DILUTED, as_of)
    quarter = quarter_rows[0] if quarter_rows else None
    notes = []
    blocked = False
    counts = [x for x in (cover, basic) if x]
    latest = max(counts, key=lambda x: (x["end"], x["filed"])) if counts else None
    def age(x):
        return (as_of - dt.date.fromisoformat(x["end"])).days if x else None
    if not latest:notes.append("Sin acciones básicas recientes identificadas en companyfacts")
    elif age(latest) > 150:notes.append("Acciones básicas con fecha superior a 150 días")
    if not quarter:notes.append("No hay media ponderada diluida trimestral 10-Q utilizable")
    elif age(quarter)>170:notes.append("Media diluida trimestral con más de 170 días")
    if ticker in MULTICLASS:
        blocked = True
        notes.append("Estructura multiclase identificada: el JSON SEC omite contextos dimensionales de algunas clases")
    cover_basic_gap = None
    if cover and basic and abs((dt.date.fromisoformat(cover["end"])-dt.date.fromisoformat(basic["end"])).days)<=50:
        cover_basic_gap = 100*(cover["value"] / basic["value"] - 1)
        if abs(cover_basic_gap) > 10:
            blocked = True
            notes.append("Diferencia >10 % entre portada y balance para fechas cercanas")
    diluted_basic_gap = None
    if latest and quarter:
        diluted_basic_gap = 100*(quarter["value"]/latest["value"]-1)
        if abs(diluted_basic_gap)>20:
            blocked = True
            notes.append("Diferencia >20 % entre media diluida trimestral y acciones básicas recientes")
        if abs((dt.date.fromisoformat(quarter["end"])-dt.date.fromisoformat(latest["end"])).days)>130:
            notes.append("La media diluida y las acciones básicas corresponden a fechas alejadas")
            blocked = True
    annual = quality.get("latest_diluted_shares")
    annual_gap = 100*(quarter["value"]/annual-1) if annual and quarter else None
    if annual_gap is not None and abs(annual_gap)>35:
        blocked = True
        notes.append("Diferencia >35 % entre media diluida trimestral y anual")
    if not quality.get("diluted_shares_proxy_available"):
        notes.append("La media anual diluida no ha superado el control histórico")
    usable = bool(latest and age(latest)<=150 and quarter and age(quarter)<=170 and not blocked
                  and quality.get("diluted_shares_proxy_available"))
    # current basic shares are NOT used for per-share DCF. Quarterly weighted
    # average diluted shares are an explicitly labeled provisional denominator.
    return {
        "status": "provisional_reconciled" if usable else "manual_review",
        "basic_cover": cover, "basic_balance": basic,
        "latest_basic": latest, "latest_quarter_diluted": quarter,
        "last_year_diluted": annual,
        "cover_vs_basic_pct": cover_basic_gap,
        "quarter_diluted_vs_basic_pct": diluted_basic_gap,
        "quarter_vs_annual_diluted_pct": annual_gap,
        "complex_multiclass": ticker in MULTICLASS,
        "notes": notes,
        "provisional_diluted_shares": quarter["value"] if usable else None,
        "provisional_source_type": "SEC XBRL 10-Q weighted-average diluted shares, NOT shares outstanding",
    }
