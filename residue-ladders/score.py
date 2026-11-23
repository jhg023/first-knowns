# score.py -- gates x throughput for the power-residue ladders (un-gameable;
# the contract is ../huntlib/scoring.py):
#
#   SCORE = p of line swept per second (in units of 10^6 p/s) on a FROZEN
#   benchmark shape, printed only if every gate is green AND the run
#   reproduces the frozen work fingerprint exactly.  Skipping work scores 0.
#
#   python score.py              full battery + the ten benchmarks
#   python score.py --bench-only the rates alone, labelled RATE: the gates
#                                did not run, so no SCORE is printed
#   python score.py --freeze     gates, then print every fingerprint
#
# The battery here is the engines' and the model's.  The campaign's own
# drills (checkpoints, interrupts, the discovery protocol) are in
# `python launch.py --selftest`, which CLAUDE.md rule 2 runs beside this.
#
# TEN frozen shapes, one production engine (residue_gpu.GpuEngine at its
# defaults), each ONE launch of 2^24 words (2^30 candidates):
#
#   SCORE            A002226 at p = 8.5*10^16: the quintic line at the
#                    median of its a(21), the first term of that family
#                    whose median clock is over a day (CLAUDE.md rule 3b).
#                    The headline, and the shape optimization rounds are
#                    measured on.
#   DAY_<entry>      the same for the other four: A002227 at 4.5*10^17
#                    (its a(18): engine v2 took a(17)'s median clock under
#                    a day), A002228 at 1.7*10^17 (a(14)), A060363 at
#                    1.6*10^17 (a(13)), A060364 at 4.3*10^17 (a(12)).
#   OPEN_<entry>     every family at p = 2^42, where the published terms
#                    end and the first open term of each is hunted (minutes
#                    of clock: checked here, not optimized).
#
# The fingerprint of a shape is every device survivor at the shape's floor
# (run 6, 5, 4, 4, 4 for the powers 5, 7, 11, 13, 17) as one word that
# binds the run to its prime (residue_gpu.bind), plus per launch the number
# of sieve survivors and of candidates that passed the first test
# (residue_gpu.fingerprint) -- so a missed prime, a changed run, two runs
# exchanged between primes, a skipped launch or a skipped stage moves the
# count or the checksum.  The sieve count belongs to the engine's sieve
# depth: a deliberate change of SIEVE_PRIMES re-freezes the shapes
# (OPTIMIZATION_LOG.md), with the survivor part unchanged.  The expectation
# was established independently of the engine being scored: the CPU engine
# (numpy sieve, Python integers, Miller-Rabin) swept the first 2^24
# candidates of every shape at its floor and gave the same primes and runs
# (BENCHMARKS.md, "The freeze"), on top of gate P1's parity at floor 1 at
# every height.
#
# No open term can sit in a benchmark window unnoticed: a prime of run above
# the family's frontier would be a discovery, and the benchmark only counts
# -- it classifies nothing.  The shapes above 2^42 are line no campaign has
# swept; their maximum run is recorded in BENCHMARKS.md and is below every
# frontier.

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from huntlib import scoring, shutdown                         # noqa: E402

# the floor of a shape: run lengths with about one prime in 10^4 of the class,
# so a launch hands the host about a thousand (a campaign hands it fewer)
FLOOR = {5: 6, 7: 5, 11: 4, 13: 4, 17: 4}
LAUNCHES = 1
# (name, power, p at the start, count, checksum): frozen 2026-11-21 for
# engine v2 (nine windows unchanged: the same 2^30 candidates and the same
# survivors as v1's two launches of 2^23 words; DAY_A002227 moved from
# 6.2*10^16 to 4.5*10^17 with its day-long filter; OPTIMIZATION_LOG.md
# round 3, BENCHMARKS.md "The freeze")
SHAPES = [
    ("SCORE", 5, 85 * 10**15, 4419, 16547262922577478245),
    ("DAY_A002227", 7, 45 * 10**16, 3587, 6643457071710258490),
    ("DAY_A002228", 11, 17 * 10**16, 4155, 16705191370555841580),
    ("DAY_A060363", 13, 16 * 10**16, 2092, 9212120557217098240),
    ("DAY_A060364", 17, 43 * 10**16, 689, 10453202450027593136),
    ("OPEN_A002226", 5, 2**42, 6069, 2988142512882649909),
    ("OPEN_A002227", 7, 2**42, 5182, 16555203898948143278),
    ("OPEN_A002228", 11, 2**42, 5587, 11204242592085098805),
    ("OPEN_A060363", 13, 2**42, 2834, 12018774250256998754),
    ("OPEN_A060364", 17, 2**42, 914, 7447129349846053348),
]


def _bench(power, p0, count, checksum, runs):
    import cupy as cp
    import numpy as np
    import residue_gpu
    e = residue_gpu._engine(power)
    sync = cp.cuda.Device().synchronize
    j0 = p0 // (2 * power)
    residue_gpu.fingerprint(e, j0, 1, FLOOR[power])            # warm: compile, pool
    sync()
    span = LAUNCHES * 64 * e.W * 2 * power
    if count is None:                                   # --freeze
        fp = residue_gpu.fingerprint(e, j0, LAUNCHES, FLOOR[power])
        return 0.0, int(fp.size), int(np.bitwise_xor.reduce(fp)), True
    rate, ok = scoring.fingerprint_benchmark(
        lambda: residue_gpu.fingerprint(e, j0, LAUNCHES, FLOOR[power]), span,
        count, checksum, runs=runs, sync=sync)
    return rate, count, checksum, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench-only", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    if not args.bench_only:
        import residue_reference
        import residue_search
        import residue_gpu
        import residue_model
        ok = residue_reference.selftest()
        ok = residue_search.selftest() and ok
        ok = residue_gpu.selftest() and ok
        ok = scoring.run_gates(residue_model.GATES) and ok
        if not ok:
            print("SCORE 0 (gates failed)")
            return 1
    if args.freeze:
        for name, power, p0, _c, _x in SHAPES:
            _, c, x, _ = _bench(power, p0, None, None, 1)
            print(f'    ("{name}", {power}, {p0}, {c}, {x}),')
        return 0
    if any(c is None for _n, _d, _p, c, _x in SHAPES):
        print("SCORE 0 (no frozen fingerprint: run --freeze on a green tree)")
        return 1
    rates = []
    for name, power, p0, c, x in SHAPES:
        rate, _, _, ok = _bench(power, p0, c, x, 5)
        if not ok:
            return 1
        rates.append((name, power, p0, rate))
    for name, power, p0, rate in rates:
        print(f"benchmark {name}: {rate:.4g} p/s (power {power}, "
              f"{LAUNCHES} launch of 2^30 candidates from p = {p0:.3g})")
        if args.bench_only:
            # no gate ran: a rate, never a SCORE (huntlib/scoring.py)
            print(f"RATE {name} {rate / 1e6:,.0f}  (gates not run)")
        elif name == "SCORE":
            scoring.emit_score(rate, unit=1e6)
        else:
            print(f"{name} {rate / 1e6:,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
