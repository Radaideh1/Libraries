"""
╔══════════════════════════════════════════════════════════════════╗
║         Signals & Systems — Interactive Signal Plotter           ║
║  Supports continuous-time and discrete-time signal visualization ║
║  + Frequency Domain (FFT) conversion                             ║
╚══════════════════════════════════════════════════════════════════╝

Dependencies:
    pip install numpy matplotlib sympy
"""

import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D


# ──────────────────────────────────────────────────────────────────
# 1.  SPECIAL FUNCTIONS
# ──────────────────────────────────────────────────────────────────

def u_continuous(t):
    """Unit step function for continuous-time signals: u(t) = 1 if t >= 0."""
    return np.where(np.asarray(t, dtype=float) >= 0, 1.0, 0.0)


def u_discrete(n):
    """Unit step function for discrete-time signals: u[n] = 1 if n >= 0."""
    return np.where(np.asarray(n, dtype=float) >= 0, 1.0, 0.0)


def delta_continuous(t, dt=0.01):
    """
    Dirac delta approximation: a narrow rectangular pulse of height 1/dt
    centred at t = 0, so the total area ≈ 1.
    """
    t = np.asarray(t, dtype=float)
    return np.where(np.abs(t) <= dt / 2, 1.0 / dt, 0.0)


def delta_discrete(n):
    """Kronecker delta: δ[n] = 1 if n == 0, else 0."""
    return np.where(np.asarray(n, dtype=float) == 0, 1.0, 0.0)


def rect(t, width=1.0):
    """Rectangular pulse: 1 for |t| <= width/2, else 0."""
    return np.where(np.abs(np.asarray(t, dtype=float)) <= width / 2, 1.0, 0.0)


def sgn(t):
    """Signum function."""
    return np.sign(np.asarray(t, dtype=float))


# ──────────────────────────────────────────────────────────────────
# 2.  EXPRESSION PRE-PROCESSING
# ──────────────────────────────────────────────────────────────────

_REPLACEMENTS_CT = [
    (r'δ\(', 'delta_c('),
    (r'delta\(', 'delta_c('),
    (r'\bu\(', 'u_c('),
    (r'\^', '**'),
    (r'(\d)(t)', r'\1*\2'),
    (r'(\d)\(', r'\1*('),
    (r'\)(t)', r')*t'),
    (r'\bpi\b', 'np.pi'),
    (r'\bsin\b', 'np.sin'),
    (r'\bcos\b', 'np.cos'),
    (r'\btan\b', 'np.tan'),
    (r'\bexp\b', 'np.exp'),
    (r'\babs\b', 'np.abs'),
    (r'\bsqrt\b', 'np.sqrt'),
    (r'\blog\b', 'np.log'),
    (r'\blog10\b', 'np.log10'),
    (r'\bsgn\b', 'sgn'),
    (r'\brect\b', 'rect'),
    (r'\bsign\b', 'np.sign'),
    (r'\bHeaviside\(', 'u_c('),
]

_REPLACEMENTS_DT = [
    (r'δ\[', 'delta_d['),
    (r'delta\[', 'delta_d['),
    (r'\bu\[', 'u_d['),
    (r'\^', '**'),
    (r'(\d)(n)', r'\1*\2'),
    (r'(\d)\[', r'\1*('),
    (r'\bpi\b', 'np.pi'),
    (r'\bsin\b', 'np.sin'),
    (r'\bcos\b', 'np.cos'),
    (r'\btan\b', 'np.tan'),
    (r'\bexp\b', 'np.exp'),
    (r'\babs\b', 'np.abs'),
    (r'\bsqrt\b', 'np.sqrt'),
    (r'\blog\b', 'np.log'),
    (r'\blog10\b', 'np.log10'),
    (r'\bsgn\b', 'sgn'),
    (r'\bsign\b', 'np.sign'),
]


def _apply_replacements(expr: str, replacements: list) -> str:
    for pattern, repl in replacements:
        expr = re.sub(pattern, repl, expr)
    return expr


def preprocess_continuous(expr: str) -> str:
    expr = expr.strip()
    expr = _apply_replacements(expr, _REPLACEMENTS_CT)
    expr = expr.replace('[', '(').replace(']', ')')
    return expr


def preprocess_discrete(expr: str) -> str:
    expr = expr.strip()
    expr = _apply_replacements(expr, _REPLACEMENTS_DT)
    expr = expr.replace('[', '(').replace(']', ')')
    return expr


# ──────────────────────────────────────────────────────────────────
# 3.  SIGNAL PARSING & EVALUATION
# ──────────────────────────────────────────────────────────────────

_CT_NAMESPACE = {
    '__builtins__': {},
    'np': np,
    'u_c': u_continuous,
    'delta_c': delta_continuous,
    'sgn': sgn,
    'rect': rect,
}

_DT_NAMESPACE = {
    '__builtins__': {},
    'np': np,
    'u_d': u_discrete,
    'delta_d': delta_discrete,
    'sgn': sgn,
}


def parse_input(raw: str):
    """
    Parse raw user input of the form:
        x(t) = <expression>   or   x[n] = <expression>

    Returns:
        (label, py_expr, signal_type)  where signal_type in {'CT', 'DT'}
    """
    raw = raw.strip()
    lhs_match = re.match(r'^[A-Za-z_]\w*[\(\[][tn][\)\]]\s*=\s*', raw)
    label = raw
    if lhs_match:
        rhs = raw[lhs_match.end():]
    else:
        rhs = raw

    has_t = bool(re.search(r'\bt\b', rhs))
    has_n = bool(re.search(r'\bn\b', rhs))

    if has_n and not has_t:
        sig_type = 'DT'
    else:
        sig_type = 'CT'

    return label, rhs, sig_type


def evaluate_signal(rhs: str, sig_type: str):
    """
    Evaluate the RHS expression over the appropriate domain.

    Returns:
        (domain_array, values_array)
    """
    if sig_type == 'CT':
        t = np.linspace(-10, 10, 4000)
        py_expr = preprocess_continuous(rhs)
        ns = dict(_CT_NAMESPACE)
        ns['t'] = t
        try:
            values = eval(py_expr, ns)
            values = np.asarray(values, dtype=float)
            if values.shape == ():
                values = np.full_like(t, float(values))
        except Exception as e:
            raise ValueError(f"Cannot evaluate expression: {e}\n"
                             f"  (processed as: {py_expr})") from e
        return t, values

    else:  # DT
        n = np.arange(-20, 21, dtype=float)
        py_expr = preprocess_discrete(rhs)
        ns = dict(_DT_NAMESPACE)
        ns['n'] = n
        try:
            values = eval(py_expr, ns)
            values = np.asarray(values, dtype=float)
            if values.shape == ():
                values = np.full_like(n, float(values))
        except Exception as e:
            raise ValueError(f"Cannot evaluate expression: {e}\n"
                             f"  (processed as: {py_expr})") from e
        return n, values


# ──────────────────────────────────────────────────────────────────
# 4.  FREQUENCY DOMAIN (FFT)
# ──────────────────────────────────────────────────────────────────

def compute_fft_ct(t: np.ndarray, values: np.ndarray):
    """
    Compute the FFT of a continuous-time signal.

    Returns:
        (freqs, magnitude, phase)
        freqs     — two-sided frequency axis in Hz
        magnitude — |X(f)|
        phase     — angle(X(f)) in degrees
    """
    dt = t[1] - t[0]
    N = len(values)
    X = np.fft.fftshift(np.fft.fft(values)) * dt   # scale by dt → approx CTFT
    freqs = np.fft.fftshift(np.fft.fftfreq(N, d=dt))
    magnitude = np.abs(X)
    phase = np.angle(X, deg=True)
    return freqs, magnitude, phase


def compute_fft_dt(n: np.ndarray, values: np.ndarray):
    """
    Compute the DTFT approximation via zero-padded FFT for a discrete-time signal.

    Returns:
        (omega, magnitude, phase)
        omega     — normalised angular frequency in [-pi, pi]
        magnitude — |X(e^{jω})|
        phase     — angle(X(e^{jω})) in degrees
    """
    N_pad = 1024                        # zero-pad for smoother spectrum
    X = np.fft.fftshift(np.fft.fft(values, n=N_pad))
    omega = np.linspace(-np.pi, np.pi, N_pad, endpoint=False)
    magnitude = np.abs(X)
    phase = np.angle(X, deg=True)
    return omega, magnitude, phase


# ──────────────────────────────────────────────────────────────────
# 5.  PLOTTING
# ──────────────────────────────────────────────────────────────────

_COLORS = ['#2196F3', '#F44336', '#4CAF50', '#FF9800',
           '#9C27B0', '#00BCD4', '#E91E63', '#607D8B']


def _style_ax(ax):
    """Apply dark theme styling to an axes object."""
    ax.set_facecolor('#1E1E2E')
    ax.tick_params(colors='#AAAAAA')
    ax.spines[:].set_color('#444444')
    ax.grid(True, color='#333355', linestyle='--', linewidth=0.6, alpha=0.8)


def plot_signals(signals: list, title_prefix: str = ''):
    """
    Plot one or more signals — time domain only.

    signals : list of (label, domain, values, sig_type)
    """
    ct_sigs = [(l, d, v) for l, d, v, st in signals if st == 'CT']
    dt_sigs = [(l, d, v) for l, d, v, st in signals if st == 'DT']

    n_axes = (1 if ct_sigs else 0) + (1 if dt_sigs else 0)
    if n_axes == 0:
        print("No signals to plot.")
        return

    fig = plt.figure(figsize=(12, 4.5 * n_axes))
    fig.patch.set_facecolor('#0F1117')

    axes = []
    if n_axes == 1:
        axes.append(fig.add_subplot(111))
    else:
        for i in range(n_axes):
            axes.append(fig.add_subplot(n_axes, 1, i + 1))

    ax_idx = 0

    if ct_sigs:
        ax = axes[ax_idx]; ax_idx += 1
        _style_ax(ax)
        ax.axhline(0, color='#555', lw=0.8)
        ax.axvline(0, color='#555', lw=0.8)
        for i, (label, t, values) in enumerate(ct_sigs):
            color = _COLORS[i % len(_COLORS)]
            ax.plot(t, values, color=color, lw=2, label=label)
        ax.set_xlabel('t  (seconds)', color='#CCCCCC', fontsize=11)
        ax.set_ylabel('Amplitude', color='#CCCCCC', fontsize=11)
        ax.set_title('Continuous-Time Signal(s)', color='#FFFFFF',
                     fontsize=13, fontweight='bold', pad=10)
        ax.legend(facecolor='#1E1E2E', edgecolor='#555',
                  labelcolor='white', fontsize=10)
        ax.set_xlim(-10, 10)

    if dt_sigs:
        ax = axes[ax_idx]; ax_idx += 1
        _style_ax(ax)
        ax.axhline(0, color='#555', lw=0.8)
        ax.axvline(0, color='#555', lw=0.8)
        for i, (label, n, values) in enumerate(dt_sigs):
            color = _COLORS[i % len(_COLORS)]
            markerline, stemlines, baseline = ax.stem(
                n, values, linefmt=color, markerfmt='o', basefmt=' ')
            markerline.set_color(color)
            markerline.set_markersize(6)
            plt.setp(stemlines, color=color, linewidth=1.5)
            proxy = Line2D([0], [0], color=color, marker='o',
                           markersize=6, label=label)
            ax.add_line(proxy)
        ax.set_xlabel('n  (samples)', color='#CCCCCC', fontsize=11)
        ax.set_ylabel('Amplitude', color='#CCCCCC', fontsize=11)
        ax.set_title('Discrete-Time Signal(s)', color='#FFFFFF',
                     fontsize=13, fontweight='bold', pad=10)
        handles = [c for c in ax.lines
                   if c.get_label() and not c.get_label().startswith('_')]
        ax.legend(handles=handles, facecolor='#1E1E2E',
                  edgecolor='#555', labelcolor='white', fontsize=10)
        ax.set_xlim(-21, 21)

    if title_prefix:
        fig.suptitle(title_prefix, color='#AAAAAA', fontsize=10, y=1.01)

    plt.tight_layout()
    plt.show()


def plot_frequency_domain(signals: list, title_prefix: str = ''):
    """
    Plot magnitude and phase spectra for one or more signals.

    signals : list of (label, domain, values, sig_type)
    """
    if not signals:
        print("No signals to transform.")
        return

    n_sigs = len(signals)
    fig = plt.figure(figsize=(14, 5 * n_sigs))
    fig.patch.set_facecolor('#0F1117')

    for idx, (label, domain, values, sig_type) in enumerate(signals):
        color = _COLORS[idx % len(_COLORS)]

        if sig_type == 'CT':
            freqs, magnitude, phase = compute_fft_ct(domain, values)
            # Limit display to ±50 Hz for readability
            mask = np.abs(freqs) <= 50
            freq_display  = freqs[mask]
            mag_display   = magnitude[mask]
            phase_display = phase[mask]
            xlabel_mag   = 'Frequency  f  (Hz)'
            xlabel_phase = 'Frequency  f  (Hz)'
            title_mag    = f'|X(f)|  —  Magnitude Spectrum  [{label}]'
            title_phase  = f'∠X(f)  —  Phase Spectrum  [{label}]'

        else:  # DT
            omega, magnitude, phase = compute_fft_dt(domain, values)
            freq_display  = omega
            mag_display   = magnitude
            phase_display = phase
            xlabel_mag   = 'Normalised Angular Frequency  ω  (rad/sample)'
            xlabel_phase = 'Normalised Angular Frequency  ω  (rad/sample)'
            title_mag    = f'|X(e^jω)|  —  Magnitude Spectrum  [{label}]'
            title_phase  = f'∠X(e^jω)  —  Phase Spectrum  [{label}]'

        # ── Magnitude ─────────────────────────────────────────────
        ax_mag = fig.add_subplot(n_sigs * 2, 1, idx * 2 + 1)
        _style_ax(ax_mag)
        ax_mag.axhline(0, color='#555', lw=0.8)
        ax_mag.axvline(0, color='#555', lw=0.8)
        ax_mag.plot(freq_display, mag_display, color=color, lw=1.8)
        ax_mag.fill_between(freq_display, mag_display,
                            alpha=0.18, color=color)
        ax_mag.set_xlabel(xlabel_mag, color='#CCCCCC', fontsize=10)
        ax_mag.set_ylabel('|X|', color='#CCCCCC', fontsize=10)
        ax_mag.set_title(title_mag, color='#FFFFFF',
                         fontsize=12, fontweight='bold', pad=8)

        # ── Phase ──────────────────────────────────────────────────
        ax_ph = fig.add_subplot(n_sigs * 2, 1, idx * 2 + 2)
        _style_ax(ax_ph)
        ax_ph.axhline(0, color='#555', lw=0.8)
        ax_ph.axvline(0, color='#555', lw=0.8)
        # Mask near-zero magnitudes to suppress noisy phase values
        threshold = 0.01 * mag_display.max() if mag_display.max() > 0 else 0
        clean_phase = np.where(mag_display > threshold, phase_display, np.nan)
        ax_ph.plot(freq_display, clean_phase,
                   color=color, lw=1.5, linestyle='--')
        ax_ph.set_xlabel(xlabel_phase, color='#CCCCCC', fontsize=10)
        ax_ph.set_ylabel('Phase (°)', color='#CCCCCC', fontsize=10)
        ax_ph.set_title(title_phase, color='#FFFFFF',
                        fontsize=12, fontweight='bold', pad=8)
        ax_ph.set_ylim(-190, 190)
        ax_ph.set_yticks([-180, -90, 0, 90, 180])

    if title_prefix:
        fig.suptitle(f'Frequency Domain — {title_prefix}',
                     color='#AAAAAA', fontsize=10, y=1.01)

    plt.tight_layout()
    plt.show()


def plot_both_domains(signals: list, title_prefix: str = ''):
    """
    Side-by-side time domain + magnitude spectrum for each signal.

    signals : list of (label, domain, values, sig_type)
    """
    if not signals:
        print("No signals to plot.")
        return

    n_sigs = len(signals)
    fig = plt.figure(figsize=(16, 4.5 * n_sigs))
    fig.patch.set_facecolor('#0F1117')

    for idx, (label, domain, values, sig_type) in enumerate(signals):
        color = _COLORS[idx % len(_COLORS)]

        # ── Time domain ───────────────────────────────────────────
        ax_t = fig.add_subplot(n_sigs, 2, idx * 2 + 1)
        _style_ax(ax_t)
        ax_t.axhline(0, color='#555', lw=0.8)
        ax_t.axvline(0, color='#555', lw=0.8)

        if sig_type == 'CT':
            ax_t.plot(domain, values, color=color, lw=2, label=label)
            ax_t.set_xlim(-10, 10)
            ax_t.set_xlabel('t  (s)', color='#CCCCCC', fontsize=10)
        else:
            markerline, stemlines, _ = ax_t.stem(
                domain, values, linefmt=color, markerfmt='o', basefmt=' ')
            markerline.set_color(color)
            markerline.set_markersize(5)
            plt.setp(stemlines, color=color, linewidth=1.5)
            ax_t.set_xlim(-21, 21)
            ax_t.set_xlabel('n  (samples)', color='#CCCCCC', fontsize=10)

        ax_t.set_ylabel('Amplitude', color='#CCCCCC', fontsize=10)
        ax_t.set_title(f'Time Domain — {label}', color='#FFFFFF',
                       fontsize=11, fontweight='bold', pad=8)
        ax_t.legend([label], facecolor='#1E1E2E',
                    edgecolor='#555', labelcolor='white', fontsize=9)

        # ── Frequency domain ──────────────────────────────────────
        ax_f = fig.add_subplot(n_sigs, 2, idx * 2 + 2)
        _style_ax(ax_f)
        ax_f.axhline(0, color='#555', lw=0.8)
        ax_f.axvline(0, color='#555', lw=0.8)

        if sig_type == 'CT':
            freqs, magnitude, _ = compute_fft_ct(domain, values)
            mask = np.abs(freqs) <= 50
            ax_f.plot(freqs[mask], magnitude[mask], color=color, lw=1.8)
            ax_f.fill_between(freqs[mask], magnitude[mask],
                              alpha=0.18, color=color)
            ax_f.set_xlabel('f  (Hz)', color='#CCCCCC', fontsize=10)
            ax_f.set_title(f'|X(f)|  Magnitude — {label}',
                           color='#FFFFFF', fontsize=11,
                           fontweight='bold', pad=8)
        else:
            omega, magnitude, _ = compute_fft_dt(domain, values)
            ax_f.plot(omega, magnitude, color=color, lw=1.8)
            ax_f.fill_between(omega, magnitude, alpha=0.18, color=color)
            ax_f.set_xlabel('ω  (rad/sample)', color='#CCCCCC', fontsize=10)
            # π tick labels
            ax_f.set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
            ax_f.set_xticklabels(['-π', '-π/2', '0', 'π/2', 'π'],
                                  color='#AAAAAA')
            ax_f.set_title(f'|X(e^jω)|  Magnitude — {label}',
                           color='#FFFFFF', fontsize=11,
                           fontweight='bold', pad=8)

        ax_f.set_ylabel('|X|', color='#CCCCCC', fontsize=10)

    if title_prefix:
        fig.suptitle(title_prefix, color='#AAAAAA', fontsize=10, y=1.01)

    plt.tight_layout()
    plt.show()


# ──────────────────────────────────────────────────────────────────
# 6.  MAIN INTERACTIVE LOOP
# ──────────────────────────────────────────────────────────────────

HELP_TEXT = """
┌─────────────────────────────────────────────────────────────────┐
│              Signals & Systems — Signal Plotter                 │
├─────────────────────────────────────────────────────────────────┤
│  Enter one signal per line (or multiple separated by  ;  )      │
│                                                                 │
│  Continuous-time examples:                                      │
│    x(t) = sin(2*pi*t)                                           │
│    x(t) = exp(-t) * u(t)                                        │
│    x(t) = exp(-t) * u(t) ; sin(2*pi*t) * u(t-1)                 │
│    x(t) = delta(t-2) + delta(t+2)                               │
│    x(t) = rect(t/2)                                             │
│    x(t) = cos(2*pi*3*t) * exp(-0.3*t)                           │
│                                                                 │
│  Discrete-time examples:                                        │
│    x[n] = (0.5)^n * u[n]                                        │
│    x[n] = delta[n] + delta[n-3]                                 │
│    x[n] = sin(2*pi*0.1*n)                                       │
│    x[n] = (0.9)^n * cos(2*pi*0.05*n) * u[n]                     │
│                                                                 │
│  Special functions:                                             │
│    u(t), u[n]       — unit step                                 │
│    delta(t), δ(t)   — Dirac delta (narrow pulse approx.)        │
│    delta[n], δ[n]   — Kronecker delta                           │
│    rect(t)          — rectangular pulse                         │
│    sgn(t)           — signum function                           │
│                                                                 │
│  Plot modes (choose after entering a signal):                   │
│    [1] Time domain only                                         │
│    [2] Frequency domain  (magnitude + phase spectra)            │
│    [3] Both side-by-side                                        │
│                                                                 │
│  Commands:  help  |  clear  |  quit                             │
└─────────────────────────────────────────────────────────────────┘
"""

MODE_PROMPT = """
  Plot mode:
    [1] Time domain only
    [2] Frequency domain  (magnitude + phase)
    [3] Both side-by-side
  Enter choice [1/2/3] (default = 1): """


def ask_plot_mode() -> str:
    """Prompt the user to choose a plot mode; returns '1', '2', or '3'."""
    try:
        choice = input(MODE_PROMPT).strip()
    except (EOFError, KeyboardInterrupt):
        return '1'
    if choice in ('2', '3'):
        return choice
    return '1'   # default to time domain


def main():
    print(HELP_TEXT)

    while True:
        try:
            raw_input_ = input("Signal> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if not raw_input_:
            continue

        cmd = raw_input_.lower()
        if cmd in ('quit', 'exit', 'q'):
            print("Goodbye!")
            sys.exit(0)
        if cmd in ('help', 'h', '?'):
            print(HELP_TEXT)
            continue
        if cmd == 'clear':
            print("\033[2J\033[H", end='')
            continue

        # Support multiple signals separated by  ;
        raw_signals = [s.strip() for s in raw_input_.split(';') if s.strip()]

        parsed = []
        ok = True
        for raw in raw_signals:
            try:
                label, rhs, sig_type = parse_input(raw)
                domain, values = evaluate_signal(rhs, sig_type)
                parsed.append((label, domain, values, sig_type))
                print(f"  ✓  [{sig_type}]  {label}")
            except ValueError as e:
                print(f"  ✗  Error parsing '{raw}':\n     {e}")
                ok = False
            except Exception as e:
                print(f"  ✗  Unexpected error for '{raw}':\n     {e}")
                ok = False

        if parsed:
            title = "  |  ".join(s[0] for s in parsed)
            mode = ask_plot_mode()

            if mode == '1':
                plot_signals(parsed, title_prefix=title)
            elif mode == '2':
                plot_frequency_domain(parsed, title_prefix=title)
            elif mode == '3':
                plot_both_domains(parsed, title_prefix=title)

        if not ok:
            print("  ⚠  Some signals could not be plotted. "
                  "Type 'help' for syntax examples.")


# ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    main()