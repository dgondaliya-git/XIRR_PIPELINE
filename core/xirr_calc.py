from scipy.optimize import newton


def xirr(cashflows, dates):
    """Calculate XIRR (Internal Rate of Return) for irregular cashflows."""
    def npv(rate):
        return sum(
            cf / (1 + rate) ** ((d - dates.iloc[0]).days / 365)
            for cf, d in zip(cashflows, dates)
        )

    try:
        return newton(npv, 0.1)
    except (RuntimeError, ValueError):
        return 0.0
