from __future__ import annotations

from dataclasses import dataclass
from itertools import product as cartesian_product

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Resource:
    name: str
    limit: float
    tolerance: float


@dataclass(frozen=True)
class Product:
    name: str
    profit: float
    demand_target: float
    demand_tolerance: float
    resources: dict[str, float]


def sample_products() -> tuple[list[Product], list[Resource]]:
    resources = [
        Resource("Modal ribu", 4200.0, 650.0),
        Resource("Jam kerja", 220.0, 35.0),
        Resource("Bahan baku kg", 420.0, 60.0),
    ]
    products = [
        Product(
            "Paket hemat",
            profit=42.0,
            demand_target=32.0,
            demand_tolerance=10.0,
            resources={"Modal ribu": 38.0, "Jam kerja": 2.0, "Bahan baku kg": 4.0},
        ),
        Product(
            "Paket reguler",
            profit=68.0,
            demand_target=24.0,
            demand_tolerance=8.0,
            resources={"Modal ribu": 58.0, "Jam kerja": 3.0, "Bahan baku kg": 6.0},
        ),
        Product(
            "Paket premium",
            profit=108.0,
            demand_target=14.0,
            demand_tolerance=6.0,
            resources={"Modal ribu": 92.0, "Jam kerja": 5.0, "Bahan baku kg": 9.0},
        ),
    ]
    return products, resources


def product_table(products: list[Product], resources: list[Resource]) -> pd.DataFrame:
    rows = []
    for product in products:
        row = {
            "Produk": product.name,
            "Profit/unit": product.profit,
            "Target permintaan": product.demand_target,
            "Toleransi permintaan": product.demand_tolerance,
        }
        for resource in resources:
            row[resource.name] = product.resources.get(resource.name, 0.0)
        rows.append(row)
    return pd.DataFrame(rows)


def resource_table(resources: list[Resource]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Sumber daya": [resource.name for resource in resources],
            "Batas ideal": [resource.limit for resource in resources],
            "Toleransi fuzzy": [resource.tolerance for resource in resources],
        }
    )


def less_equal_membership(value: float, limit: float, tolerance: float) -> float:
    if value <= limit:
        return 1.0
    if value >= limit + tolerance:
        return 0.0
    return (limit + tolerance - value) / tolerance


def greater_equal_membership(value: float, target: float, tolerance: float) -> float:
    if value >= target:
        return 1.0
    if value <= target - tolerance:
        return 0.0
    return (value - (target - tolerance)) / tolerance


def near_target_membership(value: float, target: float, tolerance: float) -> float:
    if tolerance <= 0:
        return 1.0 if value == target else 0.0
    distance = abs(value - target)
    if distance >= tolerance:
        return 0.0
    return 1.0 - (distance / tolerance)


def generate_candidate_grid(products: list[Product], resources: list[Resource], step: int) -> list[tuple[int, ...]]:
    maxima = []
    for item in products:
        resource_limits = []
        for resource in resources:
            usage = item.resources.get(resource.name, 0.0)
            if usage > 0:
                resource_limits.append((resource.limit + resource.tolerance) / usage)
        demand_limit = item.demand_target + item.demand_tolerance
        maxima.append(max(0, int(np.ceil(min(resource_limits + [demand_limit])))))

    ranges = [range(0, maximum + 1, step) for maximum in maxima]
    candidates = [tuple(int(value) for value in values) for values in cartesian_product(*ranges)]
    target_candidate = tuple(int(item.demand_target) for item in products)
    if target_candidate not in candidates:
        candidates.append(target_candidate)
    return candidates


def evaluate_plan(
    quantities: tuple[int, ...],
    products: list[Product],
    resources: list[Resource],
    min_profit_target: float,
    profit_tolerance: float,
) -> dict[str, float | str]:
    result: dict[str, float | str] = {
        "Rencana": ", ".join(f"{product.name}: {quantity}" for product, quantity in zip(products, quantities)),
        "Profit": sum(quantity * product.profit for product, quantity in zip(products, quantities)),
    }
    memberships = []

    for product, quantity in zip(products, quantities):
        degree = near_target_membership(quantity, product.demand_target, product.demand_tolerance)
        result[f"{product.name} mu permintaan"] = round(degree, 4)
        memberships.append(degree)
        result[product.name] = quantity

    for resource in resources:
        used = sum(quantity * product.resources.get(resource.name, 0.0) for product, quantity in zip(products, quantities))
        degree = less_equal_membership(used, resource.limit, resource.tolerance)
        result[f"{resource.name} terpakai"] = round(used, 4)
        result[f"{resource.name} mu"] = round(degree, 4)
        memberships.append(degree)

    profit_degree = greater_equal_membership(float(result["Profit"]), min_profit_target, profit_tolerance)
    result["mu target profit"] = round(profit_degree, 4)
    memberships.append(profit_degree)
    result["Skor fuzzy"] = round(float(min(memberships)), 4)
    result["Skor rata-rata"] = round(float(np.mean(memberships)), 4)
    return result


def optimize_plan(
    products: list[Product],
    resources: list[Resource],
    min_profit_target: float,
    profit_tolerance: float,
    step: int = 1,
) -> pd.DataFrame:
    candidates = generate_candidate_grid(products, resources, max(1, int(step)))
    rows = [evaluate_plan(candidate, products, resources, min_profit_target, profit_tolerance) for candidate in candidates]
    result = pd.DataFrame(rows)
    return result.sort_values(["Skor fuzzy", "Skor rata-rata", "Profit"], ascending=[False, False, False]).reset_index(drop=True)


def format_number_id(value: object) -> str:
    if pd.isna(value) or not isinstance(value, (int, float, np.integer, np.floating)):
        return ""
    if abs(float(value)) >= 1000:
        if float(value).is_integer():
            return f"{int(value):,}".replace(",", ".")
        whole, decimal = f"{float(value):,.2f}".split(".")
        return f"{whole.replace(',', '.')},{decimal}"
    return f"{float(value):g}"


def display_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    formatters = {column: format_number_id for column in df.select_dtypes(include="number").columns}
    return df.style.format(formatters)
