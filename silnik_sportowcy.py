
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

    # Atrybuty uzupełnione heurystycznie dla każdego sportu
    min_budget_pln: int       # miesięczny koszt startowy w PLN
    outdoor: bool             # czy sport odbywa się na zewnątrz
    involves_animals: bool    # czy wymaga kontaktu ze zwierzętami
    intensity: str            # "low" | "medium" | "high"
    min_age: int              # minimalny rozsądny wiek startowy


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
# Wczytywanie danych z CSV + wzbogacanie heurystykami
# ---------------------------------------------------------------------------

# Dodatkowe atrybuty per Sport_Code, których nie ma w CSV
_EXTRA: dict[str, dict] = {
    "AQ": dict(min_budget_pln=100,  outdoor=False, involves_animals=False, intensity="high",  min_age=5),
    "AR": dict(min_budget_pln=200,  outdoor=True,  involves_animals=False, intensity="low",   min_age=10),
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
# Silnik punktacji
# ---------------------------------------------------------------------------

def _score_physique(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """
    Porównuje wzrost i wagę użytkownika ze średnią sportowców danej dyscypliny.
    Zwraca (punkty 0–40, powody, ostrzeżenia).
    """
    reasons, warnings = [], []

    h_diff = abs(user.height_cm - sport.avg_height_cm)
    w_diff = abs(user.weight_kg - sport.avg_weight_kg)

    # Wzrost – odchylenie w procentach od średniej
    h_pct = h_diff / sport.avg_height_cm * 100
    w_pct = w_diff / sport.avg_weight_kg * 100

    # Funkcja kary: 0 odchylenia → 20 pkt, 20 % odchylenia → 0 pkt
    h_pts = max(0.0, 20 - h_pct)
    w_pts = max(0.0, 20 - w_pct)

    score = h_pts + w_pts  # max 40

    if h_pct < 5:
        reasons.append(f"Twój wzrost ({user.height_cm} cm) idealnie pasuje do średniej w {sport.name} ({sport.avg_height_cm} cm).")
    elif h_pct < 15:
        reasons.append(f"Twój wzrost jest zbliżony do typowego w {sport.name}.")
    else:
        warnings.append(f"Twój wzrost odbiega o {h_pct:.0f}% od średniej zawodników {sport.name}.")

    if w_pct < 5:
        reasons.append(f"Twoja waga ({user.weight_kg} kg) idealnie pasuje do profilu {sport.name}.")
    elif w_pct < 15:
        reasons.append(f"Twoja waga jest zbliżona do typowej w {sport.name}.")
    else:
        warnings.append(f"Twoja waga odbiega o {w_pct:.0f}% od średniej zawodników {sport.name}.")

    return score, reasons, warnings


def _score_activity(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """Dopasowanie poziomu aktywności do intensywności sportu. Max 25 pkt."""
    reasons, warnings = [], []
    order = {"low": 0, "medium": 1, "high": 2}
    diff = abs(order[user.activity_level] - order[sport.intensity])
    score = 25 - diff * 10  # 0→25, 1→15, 2→5

    if diff == 0:
        reasons.append(f"Twój poziom aktywności ({user.activity_level}) idealnie odpowiada wymaganiom {sport.name}.")
    elif diff == 1:
        reasons.append(f"Twój poziom aktywności jest zbliżony do wymagań {sport.name}.")
    else:
        warnings.append(f"Intensywność {sport.name} ({sport.intensity}) mocno różni się od Twojego poziomu aktywności.")

    return float(score), reasons, warnings


def _score_budget(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    reasons, warnings = [], []
    if user.budget_pln >= sport.min_budget_pln:
        score = 20.0
        reasons.append(f"Twój budżet ({user.budget_pln} zł/mies.) pokrywa koszty {sport.name} (min. {sport.min_budget_pln} zł/mies.).")
    else:
        ratio = user.budget_pln / sport.min_budget_pln
        score = 20.0 * ratio
        warnings.append(f"Minimalny koszt {sport.name} to ~{sport.min_budget_pln} zł/mies., a Twój budżet to {user.budget_pln} zł.")
    return score, reasons, warnings


def _score_animals(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """Bonus/kara za sporty ze zwierzętami. Max 5 pkt."""
    reasons, warnings = [], []
    if sport.involves_animals and user.like_animals:
        reasons.append(f"{sport.name} angażuje zwierzęta – idealne, bo je lubisz!")
        return 5.0, reasons, warnings
    if sport.involves_animals and not user.like_animals:
        warnings.append(f"{sport.name} wymaga pracy ze zwierzętami, a Ty ich nie lubisz.")
        return -10.0, reasons, warnings
    return 0.0, reasons, warnings


def _score_age(user: UserProfile, sport: Sport) -> tuple[float, list[str], list[str]]:
    """Czy wiek jest odpowiedni. Brak bonusu, tylko ewentualna kara."""
    reasons, warnings = [], []
    if user.age < sport.min_age:
        warnings.append(f"Zalecany wiek startowy w {sport.name} to min. {sport.min_age} lat.")
        return -15.0, reasons, warnings
    # Dla starszych użytkowników faworyzuj sporty o niskiej intensywności
    if user.age > 50 and sport.intensity == "low":
        reasons.append(f"{sport.name} to dobry wybór dla aktywnych dorosłych (niższa intensywność).")
        return 5.0, reasons, warnings
    if user.age > 50 and sport.intensity == "high":
        warnings.append(f"{sport.name} to sport o wysokiej intensywności – skonsultuj z lekarzem.")
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

    # Normalizacja do 0–100 (max teoretyczne ~90 bez bonusów za zwierzęta/wiek)
    normalized = max(0.0, min(100.0, total / 90 * 100))

    return Recommendation(
        sport=sport,
        score=round(normalized, 1),
        reasons=all_reasons,
        warnings=all_warnings,
    )


# ---------------------------------------------------------------------------
# Główna funkcja rekomendacji
# ---------------------------------------------------------------------------

def recommend(
    user: UserProfile,
    csv_path: str | Path = "sport_averages.csv",
    top_n: int = 5,
) -> list[Recommendation]:
    """
    Zwraca listę top_n rekomendowanych sportów posortowanych malejąco po score.
    """
    sports = load_sports(csv_path)
    recommendations = [score_sport(user, s) for s in sports]
    recommendations.sort(key=lambda r: r.score, reverse=True)
    return recommendations[:top_n]


# ---------------------------------------------------------------------------
# Integracja z Django (widok)
# ---------------------------------------------------------------------------

def build_profile_from_post(post_data: dict) -> UserProfile:
    """
    Tworzy UserProfile z danych przesłanych przez formularz Django (request.POST).

    Przykład użycia w views.py:
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
# CLI / demonstracja
# ---------------------------------------------------------------------------

def _print_results(results: list[Recommendation]) -> None:
    print("\n" + "=" * 60)
    print("  TOP REKOMENDOWANE SPORTY")
    print("=" * 60)
    for i, rec in enumerate(results, 1):
        sport = rec.sport
        print(f"\n#{i}  {sport.name} ({sport.code})  —  Wynik: {rec.score}/100")
        print(f"    Intensywność: {sport.intensity} | "
              f"Drużynowy: {'tak' if sport.team_sport else 'nie'} | "
              f"Min. budżet: {sport.min_budget_pln} zł/mies.")
        for r in rec.reasons:
            print(f"    ✔  {r}")
        for w in rec.warnings:
            print(f"    ⚠  {w}")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    # Przykładowy profil – możesz podać jako argumenty CLI lub zmienić poniżej
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
        # Domyślny przykład
        profile = UserProfile(
            age=28,
            height_cm=182,
            weight_kg=78,
            activity_level="high",
            budget_pln=200,
            like_animals=False,
        )
        print("Używam przykładowego profilu (wiek=28, wzrost=182cm, waga=78kg, "
              "aktywność=high, budżet=200zł, nie lubi zwierząt).")
        print("Możesz podać własne dane: python sport_recommender.py "
              "<wiek> <wzrost_cm> <waga_kg> <aktywność> <budżet_pln> <lubi_zwierzęta>")


    csv_file = Path(__file__).parent / "sport_averages.csv"
    if not csv_file.exists():
        csv_file = Path("sport_averages.csv")

    results = recommend(profile, csv_path=csv_file, top_n=5)
    _print_results(results)