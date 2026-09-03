"""score.py -- gates x fingerprinted benchmark for linear-ladders.

Prints a SCORE only if every correctness gate is green AND all six frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count
+ xor checksum of the surviving k).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

Six shapes, because one configuration is not a benchmark:

  SCORE     A088250, n = 15, the production unit wheel (..37],(37,47],(47,59]
            at unit 30030, sieve 65536, from period 1 (k = 1.92e21) -- the
            configuration the headline campaign OPENS in, and the row to
            read for opening throughput.  Denominated in kernel LAUNCHES
            rather than wheel periods because one period is 1.92e21 of k
            line (a minute of device); a launch there is ONE third-level
            residue of 7.3e9 candidates, and 24 launches are 24 of the
            1,672 residues a period holds -- just as reproducible a set of
            candidates, and a second of device.
  SCORE17   the same wheel at n = 17 -- the filter the A088250 campaign
            spends most of its wall clock at (a(15) and a(16) are expected
            within minutes; a(17)'s median is 1.7e24, hours) -- 64 launches
            of two third-level residues each (128 of the period's 1,512).
            The tables are a tenth the size of n = 15's and the line rate
            13x, so this is the row to read for the live hunt.
  SCOREM    A125838, n = 15, the unit wheel at unit 30030 -- a -1 family's
            opening filter, where the forms are r*k - 1 for r = 2..n: one
            condition fewer than A088250 at the same n, so the wheel is
            2.9x denser and the line rate a third.  A launch is one
            residue of 2.05e10 candidates; 8 of the period's 1,755.  The
            other w-class's tables are not the same tables, and this is
            where that is measured.
  SCORE2L   the k-space TWO-level wheel (23],(37] at n = 15 over 6,656 of
            ITS periods (W = 7.42e12), and
  SCORE1L   the k-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window, sweeping 33,263 times as many periods.  It must
            return the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself rather
            than as a wrong answer months later.
  SCORE10   A088250, n = 10, one-level k-space wheel to 13, sieve 4096 -- a
            filter with far more survivors per unit of line, so it weighs
            candidate throughput and the survivor path where the others
            weigh line.

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END k-line per second, the quantity the
hunt is actually paid in, divided by 1e6 for the SCORE.

Every period-denominated j0 is an exact multiple of that shape's wheel
modulus, and SCORE1L's window is deliberately the SAME ABSOLUTE WINDOW as
SCORE2L's, which is only possible because W(2L) = W(1L) * 33263.

SCORE2L, SCORE1L and SCORE10 were frozen on 2026-09-03 on the v1 engine
and reproduce unchanged on v2; SCORE, SCORE17 and SCOREM were RE-FROZEN
the same day on v2, whose wheel is the deliberate coverage change that
moves them (OPTIMIZATION_LOG.md v2, with the paired ratio against v1's
wheel on the same line).  A deliberate coverage change -- a new wheel, a
new sieve depth -- legitimately moves a fingerprint: update it in the same
commit and say why in OPTIMIZATION_LOG.md.

Wall clock: about 3 min, of which the gates are most.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import certificate                                 # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import lladder_gpu                                              # noqa: E402
import lladder_model                                            # noqa: E402
import lladder_reference                                        # noqa: E402
import lladder_search                                           # noqa: E402
from lladder_gpu import GpuEngine                               # noqa: E402

# label, family, n, p1, p2, p3, q2, j0, blocks, launches, expected count,
# xor, unit
#
# `blocks` sweeps whole wheel periods from period j0.  `launches` is for
# the launch-denominated shapes: the first `launches` kernel launches of
# period j0.
SHAPES = [
    ("SCORE",   "A088250", 15, 37,   47,   59, 65536,           1, None,   24,
     56165, 247205394479927860656, 30030),
    ("SCORE17", "A088250", 17, 37,   47,   59, 65536,           1, None,   64,
     3957, 2153040604752053900382, 30030),
    ("SCOREM",  "A125838", 15, 37,   47,   59, 65536,           1, None,    8,
     146036, 4331048872519602054736, 30030),
    ("SCORE2L", "A088250", 15, 23,   37, None, 65536,       94334, 6656, None,
     123, 706879083926370176, 1),
    # the SAME absolute window as SCORE2L: W(2L) = W(1L) * 33263 exactly, so
    # both j0 and the block count scale by that factor (written as the
    # product rather than the number, because a hand-multiplied constant
    # was once off by 200 periods in prime-ladders) -- and the SAME
    # fingerprint
    ("SCORE1L", "A088250", 15, 23, None, None, 65536,  94334 * 33263,
     6656 * 33263, None, 123, 706879083926370176, 1),
    ("SCORE10", "A088250", 10, 13, None, None,  4096,     3330003, 60000000,
     None, 1786, 1835032199166, 1),
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
    lpp = -(-eng.R3 // eng.nu)
    if launches > lpp:
        raise ValueError(f"{launches} launches exceed the {lpp} a period "
                         f"holds; denominate this shape in periods")
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
    gates = (lladder_reference.GATES + lladder_search.GATES
             + lladder_gpu.GATES + lladder_model.GATES + certificate.GATES)
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
    for (label, fam, n, p1, p2, p3, q2, j0, blocks, launches,
         count, xor, unit) in SHAPES:
        eng = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit)
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
              f"({rate_k * eng.density():.3e} candidates/s, {fam}, "
              f"filter n={n}, wheel {wheel} W={eng.W}, sieve {q2}, "
              f"fingerprint {count}/{xor})")
        print(f"{label} {rate_k / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
