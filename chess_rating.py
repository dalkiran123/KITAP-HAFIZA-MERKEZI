"""ChessOnline rating and bot roster foundation.

Pure Glicko-2 calculations. No live database mutation or automatic rating
changes until authenticated rated-match settlement is integrated.
"""
from dataclasses import dataclass
from math import exp, log, pi, sqrt

SCALE = 173.7178
TAU = 0.5

@dataclass(frozen=True)
class Rating:
    rating: float = 1500.0
    rd: float = 350.0
    volatility: float = 0.06

def update_rating(player: Rating, results, tau: float = TAU) -> Rating:
    """Apply one Glicko-2 rating period.

    results: iterable of (opponent Rating, score), score in {0, .5, 1}.
    """
    matches = list(results)
    mu = (player.rating - 1500) / SCALE
    phi = player.rd / SCALE
    sigma = player.volatility
    if not matches:
        return Rating(player.rating, min(350.0, sqrt(phi * phi + sigma * sigma) * SCALE), sigma)
    if any(score not in (0, 0.5, 1) for _, score in matches):
        raise ValueError("Invalid game score")
    def g(x):
        return 1 / sqrt(1 + 3 * x * x / (pi * pi))
    def expected(x, y, uncertainty):
        return 1 / (1 + exp(-g(uncertainty) * (x - y)))
    opponents = [((other.rating - 1500) / SCALE, other.rd / SCALE, score) for other, score in matches]
    v_inv = sum(g(p) ** 2 * expected(mu, m, p) * (1 - expected(mu, m, p)) for m, p, _ in opponents)
    v = 1 / v_inv
    delta = v * sum(g(p) * (score - expected(mu, m, p)) for m, p, score in opponents)
    a = log(sigma * sigma)
    def f(x):
        ex = exp(x)
        return ex * (delta * delta - phi * phi - v - ex) / (2 * (phi * phi + v + ex) ** 2) - (x - a) / (tau * tau)
    A = a
    if delta * delta > phi * phi + v:
        B = log(delta * delta - phi * phi - v)
    else:
        k = 1
        while f(a - k * tau) < 0:
            k += 1
        B = a - k * tau
    fA, fB = f(A), f(B)
    while abs(B - A) > 1e-6:
        C = A + (A - B) * fA / (fB - fA)
        fC = f(C)
        if fC * fB <= 0:
            A, fA = B, fB
        else:
            fA /= 2
        B, fB = C, fC
    new_sigma = exp(A / 2)
    phi_star = sqrt(phi * phi + new_sigma * new_sigma)
    new_phi = 1 / sqrt(1 / (phi_star * phi_star) + 1 / v)
    new_mu = mu + new_phi * new_phi * sum(g(p) * (score - expected(mu, m, p)) for m, p, score in opponents)
    return Rating(1500 + SCALE * new_mu, SCALE * new_phi, new_sigma)

BOT_ROSTER = tuple(
    {"id": f"chess-bot-{i:02d}", "name": f"ChessBot {i:02d}", "level": level, "is_bot": True}
    for i, level in enumerate(("beginner",) * 4 + ("intermediate",) * 3 + ("advanced",) * 3, 1)
)

def league(rating: float) -> str:
    if rating < 1200: return "Acemi"
    if rating < 1500: return "Gelişen"
    if rating < 1800: return "Orta"
    if rating < 2100: return "İleri"
    return "Usta"
