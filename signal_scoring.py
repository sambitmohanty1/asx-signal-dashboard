def calculate_signal_score_enhanced(forward_pe, peg_ratio, eps_growth, revenue_growth, analyst_upside):
    """
    Enhanced scoring for general stocks using forward-looking fundamentals.
    Each component contributes 20% to the final score.
    """
    pe_score = max(0, 100 - abs(forward_pe - 20) / 20 * 100)
    peg_score = max(0, 100 - abs(peg_ratio - 1.5) / 1.5 * 100)
    eps_score = min(100, eps_growth)
    rev_score = min(100, revenue_growth)
    upside_score = min(100, analyst_upside)

    score = (pe_score + peg_score + eps_score + rev_score + upside_score) / 5
    return round(score, 2)


def calculate_signal_score_tech(forward_pe, peg_ratio, eps_growth, revenue_growth, analyst_upside, rsi, macd_signal_alignment):
    """
    Tech-optimized scoring that reduces PE penalty and emphasizes growth/momentum.
    Weights:
    - PEG: 25%
    - EPS Growth: 20%
    - Revenue Growth: 20%
    - Analyst Upside: 15%
    - RSI: 10%
    - MACD Alignment: 10%
    """
    peg_score = max(0, 100 - abs(peg_ratio - 1.5) / 1.5 * 100)
    eps_score = min(100, eps_growth)
    rev_score = min(100, revenue_growth)
    upside_score = min(100, analyst_upside)
    rsi_score = max(0, 100 - abs(rsi - 50) / 50 * 100)
    macd_score = 100 if macd_signal_alignment else 30

    score = (peg_score * 0.25 + eps_score * 0.2 + rev_score * 0.2 +
             upside_score * 0.15 + rsi_score * 0.1 + macd_score * 0.1)
    return round(score, 2)
