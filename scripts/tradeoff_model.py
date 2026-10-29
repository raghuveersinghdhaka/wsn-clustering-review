"""Fixed versus periodic cluster-head election under the first-order radio model (Sect. 5.7, Eqs. (4)-(6),
Table 17 of the review). Analytical illustration with the parameters stated below; not a simulation.

Usage:  python scripts/tradeoff_model.py
Needs only the Python standard library. Prints the rows of Table 17 for F = 1, 5 and 10 data frames per round.
"""
import math

# radio model (Heinzelman et al., 2002)
E_elec = 50e-9          # J/bit
eps_fs = 10e-12         # J/bit/m^2
eps_mp = 0.0013e-12     # J/bit/m^4
E_DA = 5e-9             # J/bit/signal, data aggregation at the CH
d0 = math.sqrt(eps_fs / eps_mp)

# network
N, k = 100, 5           # nodes, cluster heads
M = 100.0               # field side (m)
d_BS = 100.0            # CH-to-BS distance (m)
d_b = 50.0              # range of the control broadcasts (m)
l, lc = 4000, 200       # data and control packet sizes (bits)
E0 = 0.5                # initial energy per node (J)
Ed2 = M * M / (2 * math.pi * k)   # expected squared member-to-CH distance, N nodes uniform over M x M
m = N / k - 1                     # members per cluster


def tx(bits, d2):
    """Transmit energy for an expected squared distance d2 (Eq. (1))."""
    d = math.sqrt(d2)
    return bits * (E_elec + (eps_fs * d2 if d < d0 else eps_mp * d2 * d2))


def rx(bits):
    return bits * E_elec


# Eq. (4): one set-up (re-clustering) phase, network-wide
E_setup = (2 * k * tx(lc, d_b ** 2) + (N - k) * k * rx(lc)
           + (N - k) * (tx(lc, Ed2) + 2 * rx(lc)))

rows = {}
for F in (1, 5, 10):
    E_mem = F * tx(l, Ed2)                                         # member, per round
    E_CH = F * (m * rx(l) + (m + 1) * l * E_DA + tx(l, d_BS ** 2))   # Eq. (5)
    E_steady = k * E_CH + (N - k) * E_mem
    phi = E_setup / (E_setup + E_steady)                           # Eq. (6)
    e_rot = (E_CH + m * E_mem) / (m + 1) + E_setup / N
    R_rot, R_fix = E0 / e_rot, E0 / E_CH
    rows[F] = [E_setup * 1e3, E_steady * 1e3, 100 * phi, E_CH * 1e3, E_mem * 1e3, E_CH / E_mem,
               R_rot, R_fix, R_rot / R_fix, E_CH * 1e3]

labels = ["Re-clustering energy E_setup per round (mJ)", "Steady-state network energy per round (mJ)",
          "Overhead share phi of re-clustering (%)", "CH energy E_CH per round (mJ)",
          "Member energy E_mem per round (mJ)", "Ratio E_CH / E_mem",
          "Rounds to first depletion, ideal rotation R_rot", "Rounds to depletion of a fixed battery-powered CH R_fix",
          "Lifetime ratio R_rot / R_fix (unrounded values)", "Minimum replenishment per round for a fixed CH (mJ)"]
fmt = ["{:.2f}", "{:.1f}", "{:.1f}", "{:.3g}", "{:.2f}", "{:.1f}", "{:.0f}", "{:.0f}", "{:.1f}", "{:.3g}"]
print(f"d0 = {d0:.1f} m, sqrt(E[d_m^2]) = {math.sqrt(Ed2):.1f} m, members per cluster m = {m:.0f}")
print(f"{'Quantity':58s}{'F=1':>9s}{'F=5':>9s}{'F=10':>9s}")
for i, lab in enumerate(labels):
    print(f"{lab:58s}" + "".join(f"{fmt[i].format(rows[F][i]):>9s}" for F in (1, 5, 10)))
