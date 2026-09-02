"""score.py -- gates x fingerprinted benchmark for prime-ladders.

Prints a SCORE only if every correctness gate is green AND all six frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count
+ xor checksum of the surviving k).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

Six shapes, because one configuration is not a benchmark:

  SCORE     s = +1, n = 14, the v3 UNIT wheel (..31],(31,41],(41,53] at
            unit 2310, sieve 65536, at k = 3.3e19 -- the configuration the
            A084700 campaign OPENS in, and the row to read for opening
            throughput.  It is denominated in kernel LAUNCHES rather than
            wheel periods, because one production period is 3.26e19 of k
            line and minutes at this filter; 64 launches is 64/38,610 of a
            period and just as reproducible a set of candidates.
  SCORE18   the same wheel at n = 18 -- the filter the A084700 campaign is
            RUNNING at, from the period its cursor re-denominated onto
            (1668, k = 5.44e22).  The tables are a quarter the size of
            n = 14's and the line rate 22x, so this is the row to read for
            the live hunt.
  SCORE2L   the k-space TWO-level wheel (23],(37] at n = 14, over a whole
            number of ITS periods (W = 7.42e12), and
  SCORE1L   the k-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window as SCORE2L, sweeping 33,263 times as many
            periods.  It must return the IDENTICAL fingerprint: two wheels
            enumerating the same candidates by different arithmetic, so a
            bug in the CRT lift shows up here as a mismatch inside the
            benchmark itself rather than as a wrong answer months later.
  SCOREM    s = -1, n = 12, the unit wheel at unit 210 (11 is not forced
            until n = 14), sieve 65536 -- the configuration the A084701
            campaign opens in, in launches like SCORE.  The other family's
            tables are not the same tables, and this is where that is
            measured.
  SCORE10   s = +1, n = 10, one-level k-space wheel to 13, sieve 4096 -- a
            different filter with far more survivors per unit of line, so
            it weighs candidate throughput and the survivor path where the
            others weigh line.

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END k-line per second, the quantity the
hunt is actually paid in, divided by 1e6 for the SCORE.

Every period-denominated j0 is an exact multiple of that shape's wheel
modulus, and SCORE1L's window is deliberately the SAME ABSOLUTE WINDOW as
SCORE2L's, which is only possible because W(2L) = W(1L) * 33263.

SCORE2L, SCORE1L and SCORE10 were frozen 2026-09-02 on the v1 engine and
still pin the k-space machinery.  SCORE and SCOREM were RE-FROZEN the same
day on v3, and SCORE18 added: the unit wheel keeps every survivor the v2
wheel kept over any window (G17), but a launch of it is a different subset
of candidates, so the launch-denominated shapes could not keep their old
fingerprints and were not made to (OPTIMIZATION_LOG.md, v3).  A deliberate
coverage change -- a new wheel, a new sieve depth -- legitimately moves a
fingerprint: update it in the same commit and say why there.

Wall clock: about 2 min, of which the gates are two thirds.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import certificate                                 # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import pladder_gpu                                              # noqa: E402
import pladder_model                                            # noqa: E402
import pladder_reference                                        # noqa: E402
import pladder_search                                           # noqa: E402
from pladder_gpu import GpuEngine                               # noqa: E402

# label, s, n, p1, p2, p3, q2, j0, blocks, launches, expected count, xor,
# unit
#
# `blocks` sweeps whole wheel periods from period j0.  `launches` is for
# the three-level shapes: the first `launches` kernel launches of period
# j0 -- at n = 18 that is 64 x 22 third-level residues of the 28,080 a
# unit period holds; at n = 14, 64 of 38,610.
SHAPES = [
    ("SCORE",   +1, 14, 31,   41,   53, 65536,           1, None,   64,
     26170, 32987145531510950730, 2310),
    ("SCORE18", +1, 18, 31,   41,   53, 65536,        1668, None,   64,
     729, 54348831183746127314014, 2310),
    ("SCORE2L", +1, 14, 23,   37, None, 65536,       94334, 6656, None,
     23680, 22858249279285762, 1),
    # the SAME absolute window as SCORE2L: W(2L) = W(1L) * 33263 exactly, so
    # both j0 and the block count scale by that factor (written as the
    # product rather than the number, because a hand-multiplied constant
    # was once off by 200 periods here) -- and the SAME fingerprint
    ("SCORE1L", +1, 14, 23, None, None, 65536,  94334 * 33263,
     6656 * 33263, None, 23680, 22858249279285762, 1),
    ("SCOREM",  -1, 12, 31,   41,   53, 65536,           1, None,   64,
     765063, 4432308906875442260, 210),
    ("SCORE10", +1, 10, 13, None, None,  4096,     3330003, 60000000, None,
     19004, 472865539996, 1),
]


def work_for(eng, j0, blocks, launches):
    """The benchmark's work function for one shape: a callable returning the
    sorted survivors, plus the line it covers and the units it is counted in."""
    if launches is None:
        line = blocks * eng.W

        def work():
            return eng.survivors_j(j0, j0 + blocks)
        return work, line, blocks, eng.R
    per_launch_cand = eng.R1 * eng.R2 * eng.nu
    line = launches * per_launch_cand / eng.density()

    def work():
        out = []
        it = eng.sweep(j0, j0 + 1)
        for i, (_, _, sv) in enumerate(it):
            out.extend(sv)
            if i + 1 >= launches:
                break
        it.close()
        return sorted(out)
    return work, line, launches, per_launch_cand


def main():
    gates = (pladder_reference.GATES + pladder_search.GATES
             + pladder_gpu.GATES + pladder_model.GATES + certificate.GATES)
    if not scoring.run_gates(gates):
        print("SCORE 0 (gates are not green)")
        return 1

    try:
        import cupy as cp
        sync = cp.cuda.Stream.null.synchronize
    except Exception:
        print("SCORE 0 (no GPU)")
        return 1

    ok_all = True
    for (label, s, n, p1, p2, p3, q2, j0, blocks, launches,
         count, xor, unit) in SHAPES:
        eng = GpuEngine(n, s, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit)
        work, line, units, per_unit = work_for(eng, j0, blocks, launches)
        work()                                          # warm on the window
        runs = 3 if units * per_unit > 10 ** 10 else 5
        rate_units, ok = scoring.fingerprint_benchmark(
            work, units, count, xor, runs=runs, sync=sync)
        if not ok:
            got = work()
            g = 0
            for v in got:
                g ^= int(v)
            print(f"  ({label}: got count={len(got)} xor={g})")
            ok_all = False
            continue
        rate_k = rate_units * line / units
        wheel = (f"<={p1}" if not p2 else
                 f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        if unit > 1:
            wheel += f" at unit {unit}"
        print(f"benchmark {label}: {rate_k:.3e} k/s over "
              f"[{j0 * eng.W:.4e}, +{line:.4e}) "
              f"({rate_k * eng.density():.3e} candidates/s, sign {s:+d}, "
              f"filter n={n}, wheel {wheel} W={eng.W}, sieve {q2}, "
              f"fingerprint {count}/{xor})")
        print(f"{label} {rate_k / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
