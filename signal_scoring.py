# signal_scoring.py

def calculate_signal_score_enhanced(forward_pe, peg_ratio, eps_growth, revenue_growth, analyst_upside):
    """
    Enhanced scoring for general stocks using forward-looking fundamentals.
    Weights:
        - Forward PE (normalized): 20%
        - PEG Ratio (normalized): 20%
        - EPS Growth: 20%
        - Revenue Growth: 20%
        - Analyst Upside: 20%
    """
    # Normalize PE and PEG (lower is better)
    pe_score = max(0, 100 - min(forward_pe, 100))
    peg_score = max(0, 100 - min(peg_ratio * 20, 100))  # PEG < 1 is ideal

    # Growth metrics (higher is better)
    eps_score = min(100, eps_growth)
    revenue_score = min(100, revenue_growth)

    # Analyst upside (higher is better)
    upside_score = min(100, analyst_upside)

    # Weighted average
    score = (
        pe_score * 0.2 +
        peg_score * 0.2 +
        eps_score * 0.2 +
        revenue_score * 0.2 +
        upside_score * 0.2
    )

    return round(score, 2)


def calculate_signal_score_tech(forward_pe, peg_ratio, eps_growth, revenue_growth, analyst_upside, rsi, macd_signal_alignment):
    """
    Scoring optimized for technology stocks.
    Weights:
        - PEG Ratio: 25%
        - EPS Growth: 20%
        - Revenue Growth: 20%
        - Analyst Upside: 15%
        - RSI (momentum): 10%
        - MACD Signal Alignment: 10%
    """
    # PEG score (lower is better)
    peg_score = max(0, 100 - min(peg_ratio * 20, 100))

    # Growth metrics
    eps_score = min(100, eps_growth)
    revenue_score = min(100, revenue_growth)

    # Analyst upside
    upside_score = min(100, analyst_upside)

    # RSI score (ideal range 40–70)
    if 40 <= rsi <= 70:
        rsi_score = 100
    else:
        rsi_score = max(0, 100 - abs(rsi - 55) * 2)

    # MACD signal alignment (boolean: True = aligned)
    macd_score = 100 if macd_signal_alignment else 50

    # Weighted average
    score = (
        peg_score * 0.25 +
        eps_score * 0.2 +
        revenue_score * 0.2 +
        upside_score * 0.15 +
        rsi_score * 0.1 +
        macd_score * 0.1
    )

    return round(score, 2)