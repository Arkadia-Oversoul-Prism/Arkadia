from __future__ import annotations

"""Executable transaction sheet for the Economic Seam Engine.

This module converts a lead into an auditable commercial transaction model.
It never treats a headline spread as profit and never authorizes cash movement.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


REQUIRED = (
    "commodity", "specification", "buyer", "supplier", "quantity",
    "buyer_unit_price", "supplier_unit_price", "logistics_cost",
    "other_costs", "payment_terms", "settlement_days", "capital_required",
)


@dataclass(frozen=True)
class DealSheet:
    commodity: str = ""
    specification: str = ""
    source_location: str = ""
    buyer_location: str = ""
    buyer: str = ""
    supplier: str = ""
    quantity: str = ""
    unit: str = ""
    buyer_unit_price: str = ""
    supplier_unit_price: str = ""
    logistics_cost: str = ""
    other_costs: str = ""
    payment_terms: str = ""
    settlement_days: str = ""
    capital_required: str = ""
    evidence_ids: tuple[str, ...] = ()
    eligibility_verified: bool = False
    counterparties_verified: bool = False
    prices_verified: bool = False
    logistics_verified: bool = False
    buyer_commitment_verified: bool = False
    supplier_commitment_verified: bool = False
    human_authorized: bool = False


def _money(value: str) -> Optional[Decimal]:
    try:
        if not str(value).strip():
            return None
        return Decimal(str(value).replace(",", "").replace("₦", "").strip())
    except (InvalidOperation, ValueError):
        return None


def evaluate_deal(deal: DealSheet) -> dict:
    """Return transaction economics and gates without inventing missing values."""
    missing = [field for field in REQUIRED if not str(getattr(deal, field)).strip()]
    buyer = _money(deal.buyer_unit_price)
    supplier = _money(deal.supplier_unit_price)
    logistics = _money(deal.logistics_cost)
    other = _money(deal.other_costs)
    quantity = _money(deal.quantity)
    capital = _money(deal.capital_required)

    numeric_missing = []
    for name, value in (
        ("quantity", quantity), ("buyer_unit_price", buyer),
        ("supplier_unit_price", supplier), ("logistics_cost", logistics),
        ("other_costs", other), ("capital_required", capital),
    ):
        if value is None:
            numeric_missing.append(name)

    blockers = []
    if missing or numeric_missing:
        blockers.append("Incomplete transaction sheet: " + ", ".join(dict.fromkeys(missing + numeric_missing)) + ".")
    if buyer is not None and supplier is not None and buyer <= supplier:
        blockers.append("Buyer price does not exceed supplier price before costs.")
    if not deal.prices_verified:
        blockers.append("Buyer and supplier prices are not independently verified.")
    if not deal.counterparties_verified:
        blockers.append("Buyer and supplier counterparties are not independently verified.")
    if not deal.logistics_verified:
        blockers.append("Logistics cost/path is not verified.")
    if not deal.buyer_commitment_verified:
        blockers.append("Buyer commitment is not verified.")
    if not deal.supplier_commitment_verified:
        blockers.append("Supplier commitment is not verified.")
    if not deal.eligibility_verified:
        blockers.append("Eligibility/compliance is not verified.")
    if not deal.human_authorized:
        blockers.append("Human authorization is absent. No cash deployment is authorized.")

    revenue = unit_cost = net = capital_efficiency = None
    if not numeric_missing:
        revenue = buyer * quantity
        unit_cost = (supplier * quantity) + logistics + other
        net = revenue - unit_cost
        if capital and capital > 0:
            capital_efficiency = net / capital

    executable = (
        not missing and not numeric_missing and
        not blockers
    )

    return {
        "deal": asdict(deal),
        "revenue": str(revenue) if revenue is not None else None,
        "total_cost": str(unit_cost) if unit_cost is not None else None,
        "net_realizable_spread": str(net) if net is not None else None,
        "capital_efficiency": str(capital_efficiency) if capital_efficiency is not None else None,
        "executable": executable,
        "cash_deployment_authorized": executable and deal.human_authorized,
        "blockers": blockers,
    }
