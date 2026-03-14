"""
simulator.py
------------
Financial scenario simulator for the personal finance dashboard.

This module contains pure functions that model the financial impact of
hypothetical changes — one-time expenses, new recurring costs, adjusted
savings contributions, and extra income streams.

No database access is performed here. All inputs are plain Python values
so the functions are easy to unit-test and callable from any Streamlit page.

Supported scenario_type strings
--------------------------------
"one_time_expense"        – a single non-recurring purchase or payment
"recurring_monthly_cost"  – a new cost that will repeat every month
"additional_savings"      – increasing monthly savings contributions
"reduced_savings"         – decreasing monthly savings contributions
"extra_income"            – a new recurring additional monthly income source
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _monthly_net(monthly_income: float, monthly_spending: float) -> float:
    """Return the simple monthly net (income minus spending)."""
    return monthly_income - monthly_spending


def _fmt(value: float) -> str:
    """Format a float as a signed dollar string, e.g. +$1,234.56 or -$99.00."""
    sign = "+" if value >= 0 else "-"
    return f"{sign}${abs(value):,.2f}"


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def simulate_scenario(
    scenario_type: str,
    amount: float,
    current_balance: float,
    monthly_income: float,
    monthly_spending: float,
    savings_target: float = 500.0,
) -> dict:
    """Simulate the financial impact of a hypothetical scenario.

    Parameters
    ----------
    scenario_type:
        One of the supported scenario strings listed in the module docstring.
    amount:
        Dollar amount associated with the scenario. Always treated as positive.
    current_balance:
        The user's current liquid / checking balance.
    monthly_income:
        Typical monthly take-home income.
    monthly_spending:
        Current monthly spending total, *excluding* the scenario amount.
    savings_target:
        The user's desired monthly savings amount; used to evaluate verdicts.
        Defaults to $500.

    Returns
    -------
    dict with keys:
        scenario_type    – echoed from input (str)
        amount           – echoed from input, normalised to positive (float)
        immediate_impact – one-time change to the current balance (float)
        monthly_impact   – recurring change to the monthly net cash flow (float)
        annual_impact    – 12-month estimate of the net financial effect (float)
        verdict          – short assessment label (str); one of:
                            "affordable this month"
                            "reduces monthly savings"
                            "increases financial flexibility"
                            "recurring costs becoming high"
                            "manageable one-time expense"
        details          – human-readable explanation (str)
    """
    # Normalise to a positive value regardless of what the caller passed
    amount = float(abs(amount))

    # Baseline monthly net before the scenario is applied
    current_net = _monthly_net(monthly_income, monthly_spending)

    # ------------------------------------------------------------------
    # Branch on scenario type
    # ------------------------------------------------------------------

    if scenario_type == "one_time_expense":
        # A single hit to the balance; no ongoing monthly effect.
        immediate_impact = -amount
        monthly_impact   = 0.0
        annual_impact    = -amount          # no recurrence, so 12-month = 1-time

        # Verdict: can the monthly surplus absorb the expense?
        if amount <= current_net:
            verdict = "affordable this month"
            details = (
                f"A one-time expense of ${amount:,.2f} is within your current "
                f"monthly net of {_fmt(current_net)}. Your balance would fall "
                f"from ${current_balance:,.2f} to "
                f"${current_balance - amount:,.2f}, with no long-term impact."
            )
        else:
            verdict = "manageable one-time expense"
            details = (
                f"A one-time expense of ${amount:,.2f} exceeds your monthly "
                f"surplus of {_fmt(current_net)}, but can be funded from your "
                f"balance (${current_balance:,.2f}). Consider timing it carefully "
                f"or spreading the cost if your balance is tight."
            )

    elif scenario_type == "recurring_monthly_cost":
        # Ongoing cost — no immediate balance hit, but monthly net shrinks.
        immediate_impact = 0.0
        monthly_impact   = -amount
        annual_impact    = -amount * 12

        new_net = current_net - amount      # what the monthly net becomes

        if new_net >= savings_target:
            # Budget still comfortable above the savings target
            verdict = "affordable this month"
            details = (
                f"Adding ${amount:,.2f}/month would reduce your monthly net from "
                f"{_fmt(current_net)} to {_fmt(new_net)}. You would still meet "
                f"your savings target of ${savings_target:,.2f}/month. "
                f"Annual cost: ${amount * 12:,.2f}."
            )
        elif new_net >= 0:
            # Budget still positive but savings target is at risk
            verdict = "recurring costs becoming high"
            details = (
                f"Adding ${amount:,.2f}/month brings your monthly net to "
                f"{_fmt(new_net)}, which is below your savings target of "
                f"${savings_target:,.2f}/month. You may need to cut elsewhere "
                f"to keep saving at your desired rate. Annual cost: "
                f"${amount * 12:,.2f}."
            )
        else:
            # Budget goes negative — not sustainable
            verdict = "reduces monthly savings"
            details = (
                f"Adding ${amount:,.2f}/month would put your monthly budget in "
                f"the red by {_fmt(new_net)}. Over 12 months the shortfall "
                f"would be {_fmt(annual_impact)}. Consider whether you can "
                f"offset this with a spending reduction elsewhere."
            )

    elif scenario_type == "additional_savings":
        # More money set aside each month — cash flow tighter, but wealth grows.
        immediate_impact = 0.0
        monthly_impact   = -amount          # less spendable cash each month
        annual_impact    = amount * 12      # positive: total extra saved per year

        verdict = "increases financial flexibility"
        details = (
            f"Saving an extra ${amount:,.2f}/month would reduce your available "
            f"monthly cash flow to {_fmt(current_net - amount)}, but grow your "
            f"savings by {_fmt(annual_impact)} over 12 months — building a "
            f"stronger financial cushion over time."
        )

    elif scenario_type == "reduced_savings":
        # Less saved each month — more cash now, less wealth later.
        immediate_impact = 0.0
        monthly_impact   = +amount          # more spendable cash each month
        annual_impact    = -amount * 12     # negative: total less saved per year

        verdict = "reduces monthly savings"
        details = (
            f"Saving ${amount:,.2f} less per month frees up {_fmt(amount)} in "
            f"monthly cash flow, but results in {_fmt(annual_impact)} less "
            f"saved over the next 12 months. Consider whether the short-term "
            f"relief is worth the long-term trade-off."
        )

    elif scenario_type == "extra_income":
        # Additional recurring income — improves monthly net immediately.
        immediate_impact = 0.0
        monthly_impact   = +amount
        annual_impact    = +amount * 12

        verdict = "increases financial flexibility"
        details = (
            f"An extra ${amount:,.2f}/month would raise your monthly net from "
            f"{_fmt(current_net)} to {_fmt(current_net + amount)}. "
            f"Over 12 months that adds {_fmt(annual_impact)} to your budget, "
            f"which you could direct toward savings or debt repayment."
        )

    else:
        # Unrecognised scenario — return a neutral, non-crashing result.
        immediate_impact = 0.0
        monthly_impact   = 0.0
        annual_impact    = 0.0
        verdict          = "manageable one-time expense"
        details          = (
            f"Scenario type '{scenario_type}' is not recognised. "
            f"No impact has been calculated."
        )

    return {
        "scenario_type":    scenario_type,
        "amount":           round(amount, 2),
        "immediate_impact": round(immediate_impact, 2),
        "monthly_impact":   round(monthly_impact, 2),
        "annual_impact":    round(annual_impact, 2),
        "verdict":          verdict,
        "details":          details,
    }
