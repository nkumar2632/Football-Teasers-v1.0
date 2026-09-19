"""Phase 2C — audit of the independence assumption behind `P_ticket`.

The frozen specification computes a ticket's probability as the product of its legs'
`P_est` values (`TEASER_MODEL_V1_0.md` §6). That is an independence assumption. Phase 2B
found realized ticket hit rates above the product while the legs themselves hit slightly
below their own `P_est`. This module asks whether that gap can arise from sampling noise,
from ticket overlap, or from leg-level miscalibration — or whether it requires genuine
positive dependence among legs in the same week.

**This module measures. It changes nothing.** No probability is fitted, no correction is
applied, and `P_ticket` remains the product of `P_est` values.

Two facts about the board simplify the design:

* Ticket membership is **outcome-independent**. The frozen construction ranks legs by
  `P_est` and keeps the top four, so which tickets exist is fixed before any game is
  played. A simulation can therefore hold the ticket set constant and resample only leg
  outcomes, which reproduces the historical overlap exactly.
* No week can contain two primary legs from the same game, because the primary set
  contains no complementary pair. Every same-week pair is automatically a different-game
  pair.

## Permutation schemes, declared in advance

Both schemes below were fixed before their results were computed, and both are reported
regardless of what they show.

**P1 — season-level free permutation (primary).** Within a season, permute the observed
WIN/LOSS labels among all qualifying primary legs. Preserves each season's marginal win
count exactly; destroys the association between a leg's week and its outcome. It does not
require `P_est` to be calibrated, which is the point: it asks whether wins are unusually
clustered within weeks given the season's realized win total.

**P2 — season x side_class stratified permutation (secondary).** As P1, but permuting
within (season, DOG/FAVORITE) strata, so that week-level dog/favorite composition cannot
manufacture clustering. Strata with fewer than :data:`MIN_STRATUM_SIZE` legs are held
fixed and reported.

A finer stratification (shape x total bucket) is not defensible here: seasons carry
23-63 qualifying legs, so a 16-cell stratification would leave most cells with 0-2 legs
and the permutation would be close to the identity. That limitation is stated rather than
worked around.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
import pandas as pd

#: Fixed seed for every simulation in this module.
DEFAULT_SEED = 20260919

#: Simulation count for the Monte Carlo null and both permutation schemes.
DEFAULT_SIMULATIONS = 100_000

#: Rows per simulation chunk, to bound peak memory.
CHUNK = 5_000

#: Strata smaller than this are held fixed under scheme P2.
MIN_STRATUM_SIZE = 5


# ---------------------------------------------------------------------------------------
# Block assembly
# ---------------------------------------------------------------------------------------


@dataclass
class Block:
    """One analysis block: its qualifying legs and the frozen tickets built from them.

    ``ticket_index`` maps each ticket to positions in ``legs``, so a simulation can
    regenerate exactly the historical ticket set from resampled leg outcomes.
    """

    label: str
    legs: pd.DataFrame
    tickets: pd.DataFrame
    ticket_index: dict = field(default_factory=dict)

    @property
    def p(self) -> np.ndarray:
        return self.legs["p_est"].to_numpy(dtype=float)

    @property
    def y(self) -> np.ndarray:
        return self.legs["won"].to_numpy(dtype=int)

    def observed_ticket_rate(self, size: int) -> float:
        subset = self.tickets[self.tickets["n_legs"] == size]
        return float(subset["won"].mean()) if len(subset) else float("nan")

    def n_tickets(self, size: int) -> int:
        return int((self.tickets["n_legs"] == size).sum())


def make_block(label: str, legs: pd.DataFrame, tickets: pd.DataFrame) -> Block:
    """Build a :class:`Block`, resolving each ticket's legs to row positions."""
    legs = legs.reset_index(drop=True)
    position = {leg_id: i for i, leg_id in enumerate(legs["leg_id"])}

    index: dict[int, np.ndarray] = {}
    for size in sorted(tickets["n_legs"].unique()) if len(tickets) else []:
        subset = tickets[tickets["n_legs"] == size]
        rows = [[position[leg_id] for leg_id in ids.split("|")] for ids in subset["leg_ids"]]
        index[int(size)] = np.asarray(rows, dtype=int)

    return Block(label=label, legs=legs, tickets=tickets.reset_index(drop=True), ticket_index=index)


# ---------------------------------------------------------------------------------------
# 1. Same-week residual dependence
# ---------------------------------------------------------------------------------------


def same_week_pairs(legs: pd.DataFrame) -> pd.DataFrame:
    """Every unordered pair of qualifying legs in the same (season, week), different games.

    Because no game yields two primary legs, the different-game condition never removes a
    pair; it is applied and counted anyway so the guarantee is visible in the output.
    """
    rows = []
    for (season, week), group in legs.groupby(["season", "week"]):
        records = list(group.itertuples(index=False))
        for a, b in combinations(records, 2):
            if a.game_id == b.game_id:
                continue
            rows.append(
                {
                    "season": int(season),
                    "week": int(week),
                    "leg_a": a.leg_id,
                    "leg_b": b.leg_id,
                    "p_a": float(a.p_est),
                    "p_b": float(b.p_est),
                    "y_a": int(a.won),
                    "y_b": int(b.won),
                    "resid_a": int(a.won) - float(a.p_est),
                    "resid_b": int(b.won) - float(b.p_est),
                    "resid_product": (int(a.won) - float(a.p_est)) * (int(b.won) - float(b.p_est)),
                    "joint_win": int(a.won) * int(b.won),
                    "expected_joint": float(a.p_est) * float(b.p_est),
                    "side_pair": "".join(sorted([a.side_class[0], b.side_class[0]])),
                }
            )
    return pd.DataFrame(rows)


def pair_summary(pairs: pd.DataFrame, label: str, *, seed: int = DEFAULT_SEED,
                 n_boot: int = 10_000) -> dict:
    """Summarise same-week pair dependence, with a week-clustered bootstrap interval.

    ``mean_resid_product`` estimates the average within-week covariance of outcomes. Under
    independence (and calibrated `P_est`) its expectation is zero.

    ``mean_pair_correlation`` normalises each residual product by
    ``sqrt(p_a(1-p_a) p_b(1-p_b))``, giving an average correlation-scale figure.

    The interval resamples **weeks**, not pairs, because pairs inside a week are the very
    thing under test and cannot be treated as independent draws.
    """
    if pairs.empty:
        return {
            "block": label, "n_pairs": 0, "n_weeks": 0,
            "mean_resid_product": float("nan"), "boot_ci_low": float("nan"),
            "boot_ci_high": float("nan"), "mean_pair_correlation": float("nan"),
            "observed_joint_win_rate": float("nan"), "expected_joint_win_rate": float("nan"),
            "observed_minus_expected": float("nan"),
        }

    denominator = np.sqrt(
        pairs["p_a"] * (1 - pairs["p_a"]) * pairs["p_b"] * (1 - pairs["p_b"])
    )
    correlation = float((pairs["resid_product"] / denominator).mean())

    keys = pairs[["season", "week"]].apply(tuple, axis=1)
    unique_weeks = keys.unique()
    grouped = {key: pairs.loc[keys == key, "resid_product"].to_numpy() for key in unique_weeks}

    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    week_list = list(unique_weeks)
    for i in range(n_boot):
        picked = rng.integers(0, len(week_list), size=len(week_list))
        sample = np.concatenate([grouped[week_list[j]] for j in picked])
        means[i] = sample.mean()

    return {
        "block": label,
        "n_pairs": len(pairs),
        "n_weeks": len(week_list),
        "mean_resid_product": float(pairs["resid_product"].mean()),
        "boot_ci_low": float(np.percentile(means, 2.5)),
        "boot_ci_high": float(np.percentile(means, 97.5)),
        "mean_pair_correlation": correlation,
        "observed_joint_win_rate": float(pairs["joint_win"].mean()),
        "expected_joint_win_rate": float(pairs["expected_joint"].mean()),
        "observed_minus_expected": float(
            pairs["joint_win"].mean() - pairs["expected_joint"].mean()
        ),
    }


# ---------------------------------------------------------------------------------------
# 2. Week-level all-win analysis
# ---------------------------------------------------------------------------------------


def week_all_win(legs: pd.DataFrame) -> pd.DataFrame:
    """Per-week all-win expectation under independence, against the actual outcome.

    Uses **all** qualifying legs in the week, not just the top four, per the Phase 2C
    specification of this statistic.
    """
    rows = []
    for (season, week), group in legs.groupby(["season", "week"]):
        n = len(group)
        if n < 2:
            continue
        dogs = int((group["side_class"] == "DOG").sum())
        rows.append(
            {
                "season": int(season),
                "week": int(week),
                "n_legs": n,
                "n_dogs": dogs,
                "n_favorites": n - dogs,
                "dog_fraction": dogs / n,
                "wins": int(group["won"].sum()),
                "week_hit_rate": float(group["won"].mean()),
                "expected_all_win_prob": float(group["p_est"].prod()),
                "all_win": int(group["won"].sum() == n),
                "mean_p_est": float(group["p_est"].mean()),
            }
        )
    return pd.DataFrame(rows)


def all_win_summary(weeks: pd.DataFrame, label: str) -> pd.DataFrame:
    """Expected versus actual all-win weeks, split by exact week size then overall."""
    rows = []
    groups = [("exactly 2", weeks["n_legs"] == 2), ("exactly 3", weeks["n_legs"] == 3),
              ("exactly 4", weeks["n_legs"] == 4), (">=5", weeks["n_legs"] >= 5),
              ("all weeks >=2", weeks["n_legs"] >= 2)]
    for name, mask in groups:
        subset = weeks[mask]
        rows.append(
            {
                "block": label,
                "week_size": name,
                "weeks": len(subset),
                "expected_all_win_weeks": float(subset["expected_all_win_prob"].sum()),
                "actual_all_win_weeks": int(subset["all_win"].sum()),
                "actual_minus_expected": float(
                    subset["all_win"].sum() - subset["expected_all_win_prob"].sum()
                ),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# 3. Monte Carlo null with the exact historical board
# ---------------------------------------------------------------------------------------


def _ticket_wins(outcomes: np.ndarray, index: np.ndarray) -> np.ndarray:
    """Count winning tickets per simulation. ``outcomes`` is (sims, legs) boolean."""
    if index.size == 0:
        return np.zeros(outcomes.shape[0], dtype=int)
    per_ticket = outcomes[:, index[:, 0]]
    for column in range(1, index.shape[1]):
        per_ticket = per_ticket & outcomes[:, index[:, column]]
    return per_ticket.sum(axis=1)


def _all_win_weeks(outcomes: np.ndarray, week_groups: list) -> np.ndarray:
    counts = np.zeros(outcomes.shape[0], dtype=int)
    for positions in week_groups:
        counts += outcomes[:, positions].all(axis=1)
    return counts


def _week_groups(legs: pd.DataFrame) -> list:
    groups = []
    for _, group in legs.reset_index(drop=True).groupby(["season", "week"]):
        if len(group) >= 2:
            groups.append(group.index.to_numpy())
    return groups


def monte_carlo_null(block: Block, *, n_sims: int = DEFAULT_SIMULATIONS,
                     seed: int = DEFAULT_SEED) -> dict:
    """Simulate the block under independent Bernoulli(P_est) leg outcomes.

    The historical ticket set is held fixed, so ticket overlap is reproduced exactly: if
    four legs generated six 2-team and four 3-team tickets historically, the simulation
    generates those same overlapping tickets from the simulated leg outcomes.

    This null assumes `P_est` is correctly calibrated; the permutation test does not.
    """
    p = block.p
    rng = np.random.default_rng(seed)
    week_groups = _week_groups(block.legs)

    sizes = [size for size in (2, 3) if size in block.ticket_index]
    totals = {size: block.ticket_index[size].shape[0] for size in sizes}
    wins = {size: np.empty(n_sims, dtype=int) for size in sizes}
    all_wins = np.empty(n_sims, dtype=int)
    leg_wins = np.empty(n_sims, dtype=int)

    done = 0
    while done < n_sims:
        take = min(CHUNK, n_sims - done)
        outcomes = rng.random((take, p.size)) < p
        for size in sizes:
            wins[size][done:done + take] = _ticket_wins(outcomes, block.ticket_index[size])
        all_wins[done:done + take] = _all_win_weeks(outcomes, week_groups)
        leg_wins[done:done + take] = outcomes.sum(axis=1)
        done += take

    result = {"block": block.label, "n_sims": n_sims, "seed": seed}
    for size in (2, 3):
        if size not in totals or totals[size] == 0:
            continue
        rates = wins[size] / totals[size]
        observed = block.observed_ticket_rate(size)
        result[f"{size}team"] = {
            "n_tickets": totals[size],
            "observed_hit_rate": observed,
            "sim_mean": float(rates.mean()),
            "sim_ci_low": float(np.percentile(rates, 2.5)),
            "sim_ci_high": float(np.percentile(rates, 97.5)),
            "p_value_one_sided": float((1 + np.sum(rates >= observed)) / (1 + n_sims)),
        }

    observed_all_win = int(
        week_all_win(block.legs).query("n_legs >= 2")["all_win"].sum()
    ) if week_groups else 0
    result["all_win_weeks"] = {
        "weeks": len(week_groups),
        "observed": observed_all_win,
        "sim_mean": float(all_wins.mean()),
        "sim_ci_low": float(np.percentile(all_wins, 2.5)),
        "sim_ci_high": float(np.percentile(all_wins, 97.5)),
        "p_value_one_sided": float((1 + np.sum(all_wins >= observed_all_win)) / (1 + n_sims)),
    }
    observed_leg_wins = int(block.y.sum())
    result["leg_wins"] = {
        "observed": observed_leg_wins,
        "sim_mean": float(leg_wins.mean()),
        "sim_ci_low": float(np.percentile(leg_wins, 2.5)),
        "sim_ci_high": float(np.percentile(leg_wins, 97.5)),
    }
    return result


# ---------------------------------------------------------------------------------------
# 4. Calibration-neutral permutation
# ---------------------------------------------------------------------------------------


def _strata_positions(legs: pd.DataFrame, scheme: str) -> list:
    """Row positions defining each permutation stratum. See the module docstring."""
    frame = legs.reset_index(drop=True)
    if scheme == "P1":
        keys = ["season"]
    elif scheme == "P2":
        keys = ["season", "side_class"]
    else:
        raise ValueError(f"unknown permutation scheme {scheme!r}")
    return [group.index.to_numpy() for _, group in frame.groupby(keys)]


def permutation_test(block: Block, *, scheme: str = "P1",
                     n_sims: int = DEFAULT_SIMULATIONS, seed: int = DEFAULT_SEED) -> dict:
    """Permute observed outcomes among qualifying legs, then rebuild the frozen tickets.

    Marginal win counts are preserved exactly inside each stratum, so the test does not
    assume `P_est` is calibrated. It asks only whether the realized wins are more clustered
    within weeks than a random reallocation of the same wins would produce.

    Under P2, strata smaller than :data:`MIN_STRATUM_SIZE` are held fixed; the count of
    held-fixed legs is returned so the limitation is visible.
    """
    y = block.y.astype(bool)
    strata = _strata_positions(block.legs, scheme)
    permutable = [s for s in strata if s.size >= MIN_STRATUM_SIZE]
    held_fixed = sum(s.size for s in strata if s.size < MIN_STRATUM_SIZE)

    rng = np.random.default_rng(seed)
    week_groups = _week_groups(block.legs)
    sizes = [size for size in (2, 3) if size in block.ticket_index]
    totals = {size: block.ticket_index[size].shape[0] for size in sizes}
    wins = {size: np.empty(n_sims, dtype=int) for size in sizes}
    all_wins = np.empty(n_sims, dtype=int)

    done = 0
    while done < n_sims:
        take = min(CHUNK, n_sims - done)
        outcomes = np.tile(y, (take, 1))
        for positions in permutable:
            block_values = outcomes[:, positions]
            order = rng.random(block_values.shape).argsort(axis=1)
            outcomes[:, positions] = np.take_along_axis(block_values, order, axis=1)
        for size in sizes:
            wins[size][done:done + take] = _ticket_wins(outcomes, block.ticket_index[size])
        all_wins[done:done + take] = _all_win_weeks(outcomes, week_groups)
        done += take

    result = {
        "block": block.label,
        "scheme": scheme,
        "n_sims": n_sims,
        "seed": seed,
        "strata": len(strata),
        "permutable_strata": len(permutable),
        "legs_held_fixed": held_fixed,
        "n_legs": int(block.legs.shape[0]),
    }
    for size in (2, 3):
        if size not in totals or totals[size] == 0:
            continue
        rates = wins[size] / totals[size]
        observed = block.observed_ticket_rate(size)
        result[f"{size}team"] = {
            "n_tickets": totals[size],
            "observed_hit_rate": observed,
            "perm_mean": float(rates.mean()),
            "perm_ci_low": float(np.percentile(rates, 2.5)),
            "perm_ci_high": float(np.percentile(rates, 97.5)),
            "p_value_one_sided": float((1 + np.sum(rates >= observed)) / (1 + n_sims)),
        }
    observed_all_win = int(week_all_win(block.legs).query("n_legs >= 2")["all_win"].sum()) if week_groups else 0
    result["all_win_weeks"] = {
        "weeks": len(week_groups),
        "observed": observed_all_win,
        "perm_mean": float(all_wins.mean()),
        "perm_ci_low": float(np.percentile(all_wins, 2.5)),
        "perm_ci_high": float(np.percentile(all_wins, 97.5)),
        "p_value_one_sided": float((1 + np.sum(all_wins >= observed_all_win)) / (1 + n_sims)),
    }
    return result


# ---------------------------------------------------------------------------------------
# 5. Overlap and cluster-aware uncertainty
# ---------------------------------------------------------------------------------------


def overlap_stats(block: Block) -> dict:
    """Quantify how far the nominal ticket count overstates independent information."""
    tickets = block.tickets
    if tickets.empty:
        return {"block": block.label, "unique_qualifying_legs": len(block.legs),
                "n_tickets_2team": 0, "n_tickets_3team": 0, "weeks_contributing_tickets": 0,
                "legs_used_on_tickets": 0, "mean_tickets_per_used_leg": float("nan"),
                "max_tickets_containing_one_leg": 0}

    appearances: dict[str, int] = {}
    for ids in tickets["leg_ids"]:
        for leg_id in ids.split("|"):
            appearances[leg_id] = appearances.get(leg_id, 0) + 1

    counts = np.array(list(appearances.values()))
    return {
        "block": block.label,
        "unique_qualifying_legs": len(block.legs),
        "n_tickets_2team": block.n_tickets(2),
        "n_tickets_3team": block.n_tickets(3),
        "weeks_contributing_tickets": int(
            tickets[["season", "week"]].drop_duplicates().shape[0]
        ),
        "legs_used_on_tickets": len(appearances),
        "mean_tickets_per_used_leg": float(counts.mean()),
        "max_tickets_containing_one_leg": int(counts.max()),
    }


def week_bootstrap_ticket_rate(block: Block, size: int, *, n_boot: int = 10_000,
                               seed: int = DEFAULT_SEED) -> dict:
    """Cluster-aware interval for a ticket hit rate, resampling **weeks** with replacement.

    Tickets inside a week share legs and, under the hypothesis being tested, share a common
    shock. Treating them as independent would understate the interval, so the resampling
    unit is the week.
    """
    tickets = block.tickets[block.tickets["n_legs"] == size]
    if tickets.empty:
        return {"block": block.label, "ticket_size": f"{size}-team", "n_tickets": 0,
                "observed_hit_rate": float("nan"), "boot_ci_low": float("nan"),
                "boot_ci_high": float("nan"), "n_weeks": 0}

    keys = tickets[["season", "week"]].apply(tuple, axis=1)
    week_list = list(keys.unique())
    grouped = {key: tickets.loc[keys == key, "won"].to_numpy() for key in week_list}

    rng = np.random.default_rng(seed)
    rates = np.empty(n_boot)
    for i in range(n_boot):
        picked = rng.integers(0, len(week_list), size=len(week_list))
        sample = np.concatenate([grouped[week_list[j]] for j in picked])
        rates[i] = sample.mean()

    return {
        "block": block.label,
        "ticket_size": f"{size}-team",
        "n_tickets": len(tickets),
        "n_weeks": len(week_list),
        "observed_hit_rate": float(tickets["won"].mean()),
        "boot_ci_low": float(np.percentile(rates, 2.5)),
        "boot_ci_high": float(np.percentile(rates, 97.5)),
    }
