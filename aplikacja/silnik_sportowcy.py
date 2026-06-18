import csv
import math
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Sport:
    code: str
    name: str
    avg_height_cm: float
    avg_weight_kg: float
    team_sport: bool

    # Attributes added heuristically for each sport
    min_budget_pln: int       # minimum monthly cost in PLN
    outdoor: bool             # whether the sport is played outdoors
    involves_animals: bool    # whether it requires contact with animals
    intensity: str            # "low" | "medium" | "high"
    min_age: int              # reasonable minimum starting age


@dataclass
class UserProfile:
    age: int
    height_cm: float
    weight_kg: float
    activity_level: str   # "low" | "medium" | "high"
    budget_pln: int
    like_animals: bool


@dataclass
class Recommendation:
    sport: Sport
    score: float
    reasons: list[str]
    warnings: list[str]


# ---------------------------------------------------------------------------
# Loading data from CSV + enriching with heuristics
# ---------------------------------------------------------------------------

# Extra attributes per Sport_Code, not present in the CSV
_EXTRA: dict[str, dict] = {
    "AQ": dict(min_budget_pln=100,  outdoor=False, involves_animals=False, intensity="high",  min_age=5),
    "AR": dict(min_budget_pln=200,  outdoor=True,  involves_animals=False, intensity="medium",   min_age=10),
    "AT": dict(min_budget_pln=50,   outdoor=True,  involves_animals=False, intensity="high",  min_age=8),
    "BD": dict(min_budget_pln=80,   outdoor=False, involves_animals=False, intensity="medium",min_age=6),
    "BK": dict(min_budget_pln=100,  outdoor=False, involves_animals=False, intensity="high",  min_age=8),
    "BX": dict(min_budget_pln=150,  outdoor=False, involves_animals=False, intensity="high",  min_age=12),
    "CY": dict(min_budget_pln=300,  outdoor=True,  involves_animals=False, intensity="high",  min_age=6),
    "EQ": dict(min_budget_pln=800,  outdoor=True,  involves_animals=True,  intensity="medium",min_age=6),
    "FB": dict(min_budget_pln=80,   outdoor=True,  involves_animals=False, intensity="high",  min_age=6),
    "FE": dict(min_budget_pln=250,  outdoor=False, involves_animals=False, intensity="medium",min_age=8),
    "GO": dict(min_budget_pln=400,  outdoor=True,  involves_animals=False, intensity="low",   min_age=8),
    "GY": dict(min_budget_pln=150,  outdoor=False, involves_animals=False, intensity="high",  min_age=4),
    "HB": dict(min_budget_pln=100,  outdoor=False, involves_animals=False, intensity="high",  min_age=8),
    "HO": dict(min_budget_pln=150,  outdoor=True,  involves_animals=False, intensity="high",  min_age=8),
    "IH": dict(min_budget_pln=300,  outdoor=False, involves_animals=False, intensity="high",  min_age=5),
    "JU": dict(min_budget_pln=120,  outdoor=False, involves_animals=False, intensity="high",  min_age=6),
    "MP": dict(min_budget_pln=500,  outdoor=True,  involves_animals=True,  intensity="high",  min_age=14),
    "RO": dict(min_budget_pln=200,  outdoor=True,  involves_animals=False, intensity="high",  min_age=12),
    "RU": dict(min_budget_pln=100,  outdoor=True,  involves_animals=False, intensity="high",  min_age=10),
    "SA": dict(min_budget_pln=500,  outdoor=True,  involves_animals=False, intensity="medium",min_age=8),
    "SB": dict(min_budget_pln=150,  outdoor=True,  involves_animals=False, intensity="medium",min_age=6),
    "SH": dict(min_budget_pln=300,  outdoor=True,  involves_animals=False, intensity="low",   min_age=12),
    "SI": dict(min_budget_pln=400,  outdoor=True,  involves_animals=False, intensity="high",  min_age=5),
    "SK": dict(min_budget_pln=200,  outdoor=False, involves_animals=False, intensity="medium",min_age=5),
    "TE": dict(min_budget_pln=150,  outdoor=True,  involves_animals=False, intensity="medium",min_age=6),
    "TK": dict(min_budget_pln=120,  outdoor=False, involves_animals=False, intensity="high",  min_age=5),
    "TT": dict(min_budget_pln=60,   outdoor=False, involves_animals=False, intensity="medium",min_age=6),
    "VB": dict(min_budget_pln=100,  outdoor=True,  involves_animals=False, intensity="high",  min_age=8),
    "WL": dict(min_budget_pln=100,  outdoor=False, involves_animals=False, intensity="high",  min_age=14),
    "WR": dict(min_budget_pln=100,  outdoor=False, involves_animals=False, intensity="high",  min_age=8),
}


def load_sports(csv_path: str | Path) -> list[Sport]:
    sports = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["Sport_Code"].strip()
            extra = _EXTRA.get(code, {})
            sports.append(Sport(
                code=code,
                name=row["Sport_Name"].strip(),
                avg_height_cm=float(row["Avg_Height_cm"]),
                avg_weight_kg=float(row["Avg_Weight_kg"]),
                team_sport=(row["Sport_Group"].strip().lower() == "yes"),
                min_budget_pln=extra.get("min_budget_pln", 200),
                outdoor=extra.get("outdoor", False),
                involves_animals=extra.get("involves_animals", False),
                intensity=extra.get("intensity", "medium"),
                min_age=extra.get("min_age", 6),
            ))
    return sports


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def _score_physique(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """
    Compares the user's height and weight against the average for athletes in this sport.
    Returns (points 0-40, reasons, warnings).
    """
    reasons, warnings = [], []

    h_diff = abs(user.height_cm - sport.avg_height_cm)
    w_diff = abs(user.weight_kg - sport.avg_weight_kg)

    # Height - percentage deviation from the average
    h_pct = h_diff / sport.avg_height_cm * 100
    w_pct = w_diff / sport.avg_weight_kg * 100

    # Penalty function: 0% deviation -> 20 pts, 20% deviation -> 0 pts
    h_pts = max(0.0, 20 - h_pct)
    w_pts = max(0.0, 20 - w_pct)

    score = h_pts + w_pts  # max 40

    if h_pct < 5:
        reasons.append(f"Your height ({user.height_cm} cm) is a great match for the {sport.name} average ({sport.avg_height_cm} cm).")
    elif h_pct < 15:
        reasons.append(f"Your height is close to the typical range for {sport.name}.")
    else:
        warnings.append(f"Your height deviates by {h_pct:.0f}% from the average {sport.name} athlete.")

    if w_pct < 5:
        reasons.append(f"Your weight ({user.weight_kg} kg) is a great match for the {sport.name} profile.")
    elif w_pct < 15:
        reasons.append(f"Your weight is close to the typical range for {sport.name}.")
    else:
        warnings.append(f"Your weight deviates by {w_pct:.0f}% from the average {sport.name} athlete.")

    return score, reasons, warnings


def _score_activity(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """Match between the user's activity level and the sport's intensity. Max 25 pts."""
    reasons, warnings = [], []
    order = {"low": 0, "medium": 1, "high": 2}
    diff = abs(order[user.activity_level] - order[sport.intensity])
    score = 25 - diff * 10  # 0->25, 1->15, 2->5

    if diff == 0:
        reasons.append(f"Your activity level ({user.activity_level}) is a perfect match for {sport.name}.")
    elif diff == 1:
        reasons.append(f"Your activity level is reasonably close to what {sport.name} requires.")
    else:
        warnings.append(f"The intensity of {sport.name} ({sport.intensity}) is quite different from your activity level.")

    return float(score), reasons, warnings


def _score_budget(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    reasons, warnings = [], []
    if user.budget_pln >= sport.min_budget_pln:
        score = 20.0
        reasons.append(f"Your budget ({user.budget_pln} PLN/month) covers the cost of {sport.name} (min. {sport.min_budget_pln} PLN/month).")
    else:
        ratio = user.budget_pln / sport.min_budget_pln
        score = 20.0 * ratio
        warnings.append(f"The minimum cost for {sport.name} is ~{sport.min_budget_pln} PLN/month, but your budget is {user.budget_pln} PLN.")
    return score, reasons, warnings


def _score_animals(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """Bonus/penalty for sports involving animals. Max 5 pts."""
    reasons, warnings = [], []
    if sport.involves_animals and user.like_animals:
        reasons.append(f"{sport.name} involves animals - a great fit since you like them!")
        return 5.0, reasons, warnings
    if sport.involves_animals and not user.like_animals:
        warnings.append(f"{sport.name} requires working with animals, and you don't like them.")
        return -10.0, reasons, warnings
    return 0.0, reasons, warnings


def _score_age(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """Whether the age is appropriate. No bonus, only a possible penalty."""
    reasons, warnings = [], []
    if user.age < sport.min_age:
        warnings.append(f"The recommended starting age for {sport.name} is at least {sport.min_age} years.")
        return -15.0, reasons, warnings
    # Favor low-intensity sports for older users
    if user.age > 50 and sport.intensity == "low":
        reasons.append(f"{sport.name} is a great choice for active adults (lower intensity).")
        return 5.0, reasons, warnings
    if user.age > 50 and sport.intensity == "high":
        warnings.append(f"{sport.name} is a high-intensity sport - consider checking with a doctor.")
    return 0.0, reasons, warnings


def score_sport(user: UserProfile, sport: Sport) -> Recommendation:
    total = 0.0
    all_reasons: list[str] = []
    all_warnings: list[str] = []

    for fn in [_score_physique, _score_activity, _score_budget, _score_animals, _score_age]:
        pts, r, w = fn(user, sport)
        total += pts
        all_reasons.extend(r)
        all_warnings.extend(w)

    # Normalize to 0-100 (theoretical max ~90 without animal/age bonuses)
    normalized = max(0.0, min(100.0, total / 90 * 100))

    return Recommendation(
        sport=sport,
        score=round(normalized, 1),
        reasons=all_reasons,
        warnings=all_warnings,
    )


# ---------------------------------------------------------------------------
# Main recommendation function
# ---------------------------------------------------------------------------

def recommend(
    user: UserProfile,
    csv_path: str | Path = "sport_averages.csv",
    top_n: int = 5,
) -> list[Recommendation]:
    """
    Returns a list of the top_n recommended sports, sorted by score in descending order.
    """
    sports = load_sports(csv_path)
    recommendations = [score_sport(user, s) for s in sports]
    recommendations.sort(key=lambda r: r.score, reverse=True)
    return recommendations[:top_n]


# ---------------------------------------------------------------------------
# Django integration (view)
# ---------------------------------------------------------------------------

def build_profile_from_post(post_data: dict) -> UserProfile:
    """
    Builds a UserProfile from data submitted through the Django form (request.POST).

    Example usage in views.py:
        from sport_recommender import build_profile_from_post, recommend

        def submit_form(request):
            if request.method == "POST":
                user = build_profile_from_post(request.POST)
                results = recommend(user, csv_path="sport_averages.csv", top_n=5)
                return render(request, "results.html", {"results": results})
    """
    return UserProfile(
        age=int(post_data.get("age", 0)),
        height_cm=float(post_data.get("height", 170)),
        weight_kg=float(post_data.get("weight", 70)),
        activity_level=post_data.get("activity_level", "medium"),
        budget_pln=int(post_data.get("budget", 100)),
        like_animals=post_data.get("like_animals", "no") == "yes",
    )


# ---------------------------------------------------------------------------
# CLI / demo
# ---------------------------------------------------------------------------

def _print_results(results: list[Recommendation]) -> None:
    print("\n" + "=" * 60)
    print("  TOP RECOMMENDED SPORTS")
    print("=" * 60)
    for i, rec in enumerate(results, 1):
        sport = rec.sport
        print(f"\n#{i}  {sport.name} ({sport.code})  -  Score: {rec.score}/100")
        print(f"    Intensity: {sport.intensity} | "
              f"Team sport: {'yes' if sport.team_sport else 'no'} | "
              f"Min. budget: {sport.min_budget_pln} PLN/month")
        for r in rec.reasons:
            print(f"    +  {r}")
        for w in rec.warnings:
            print(f"    !  {w}")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    # Example profile - you can pass it as CLI arguments or edit it below
    if len(sys.argv) == 7:
        profile = UserProfile(
            age=int(sys.argv[1]),
            height_cm=float(sys.argv[2]),
            weight_kg=float(sys.argv[3]),
            activity_level=sys.argv[4],          # low / medium / high
            budget_pln=int(sys.argv[5]),
            like_animals=sys.argv[6].lower() == "yes",
        )
    else:
        # Default example
        profile = UserProfile(
            age=28,
            height_cm=182,
            weight_kg=78,
            activity_level="high",
            budget_pln=200,
            like_animals=False,
        )
        print("Using the default profile (age=28, height=182cm, weight=78kg, "
              "activity=high, budget=200 PLN, doesn't like animals).")
        print("You can pass your own data: python sport_recommender.py "
              "<age> <height_cm> <weight_kg> <activity> <budget_pln> <likes_animals>")


    csv_file = Path(__file__).parent / "sport_averages_final.csv"
    if not csv_file.exists():
        csv_file = Path("sport_averages_final.csv")

    results = recommend(profile, csv_path=csv_file, top_n=5)
    _print_results(results)