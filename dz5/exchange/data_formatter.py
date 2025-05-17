def format_currency_data(data: dict, date: str, currencies: list) -> dict:
    result = {}
    for entry in data.get("exchangeRate", []):
        if entry.get("currency") in currencies:
            result.setdefault(date, {})
            result[date][entry["currency"]] = {
                "sale": entry.get("saleRate", entry.get("saleRateNB")),
                "purchase": entry.get("purchaseRate", entry.get("purchaseRateNB")),
            }
    return result
