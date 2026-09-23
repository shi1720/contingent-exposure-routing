"""Constructed financial arithmetic; ground truth never uses a model."""
import json
import numpy as np
from decimal import Decimal, getcontext

getcontext().prec = 40


def exact_trade(nav, risky, target, fee):
    nav, risky, target, fee = map(lambda x: Decimal(str(x)), (nav, risky, target, fee))
    gap = target*nav-risky
    sign = Decimal(1) if gap >= 0 else Decimal(-1)
    return gap / (1+target*fee*sign)


def generate_tasks(seed=1720406, count=256):
    rng = np.random.default_rng(seed)
    tasks = []
    for i in range(count):
        nav = int(rng.integers(20, 501))*1000
        initial = int(rng.integers(5, 146))/100
        target = int(rng.integers(10, 141))/100
        risky = round(nav*initial, 2)
        cash = round(nav-risky, 2)
        fee_bps = int(rng.choice([5, 15, 35, 75, 150, 300]))
        fee = fee_bps/10000
        framing = [
            "A portfolio has a risky position worth ${risky:,.2f} and cash of ${cash:,.2f}.",
            "An account's pre-trade NAV is ${nav:,.2f}; its risky holding is ${risky:,.2f}.",
            "The risky sleeve is ${risky:,.2f}. Cash (negative means borrowing) is ${cash:,.2f}.",
            "At unchanged mid-prices, total equity is ${nav:,.2f}, including risky exposure ${risky:,.2f}."
        ][i % 4].format(risky=risky,cash=cash,nav=nav)
        prompt = (framing + f" Rebalance to risky exposure equal to {target*100:.0f}% of POST-TRADE NAV. "
                  f"Transaction fees are {fee_bps} basis points of the absolute mid-price trade notional and are paid out of the account. "
                  "There is no price movement, tax, spread beyond this fee, or other cash flow. Borrowing and shorting are allowed. "
                  "Find the signed dollar trade notional at mid-price (positive for buy, negative for sell), accounting for fees reducing NAV. "
                  'Return only a JSON object with a numeric field "trade_dollars", rounded to the nearest cent.')
        tasks.append(dict(id=f"rebalance-{i:04d}",nav=nav,risky=risky,cash=cash,target=target,
                          fee=fee,fee_bps=fee_bps,template=i % 4,prompt=prompt,
                          exact_trade=str(exact_trade(nav,risky,target,fee))))
    # Fixed shuffled split, independent of all responses.
    order = np.random.default_rng(seed+1).permutation(count)
    calibration = set(order[:count//2].tolist())
    for i, task in enumerate(tasks):
        task["split"] = "calibration" if i in calibration else "test"
    return tasks


def parse_trade(text):
    try:
        obj = json.loads(text)
        value = obj["trade_dollars"]
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not np.isfinite(value):
            raise ValueError("not a finite number")
        return float(value), True
    except (TypeError,ValueError,KeyError):
        return 0., False
