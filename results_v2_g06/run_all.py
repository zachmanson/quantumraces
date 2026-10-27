#!/usr/bin/env python3
"""
Overnight batch for gamma_S = 0.6 (ticket 01, first-finder fork rule). Runs unattended:

  1. headline c = 1, 2 (both regimes)     4. headline c = 3, 4 (both regimes)
  2. gamma_S sweep c = 1, 2               5. gamma_S sweep c = 3, 4
  3. no-quantum-miner control             6. c = 3 second equilibria (stop_after = 2, both regimes, untimed)

Each configuration is its own run.py process with a wall-clock limit (3 h, except step 6). On a timeout the
whole process tree is killed, the stage it reached is logged, and the batch moves on; a crashed configuration
(e.g. killed for low memory) is recorded the same way. README.md is rewritten after every configuration.

  python results_v2_g06/run_all.py            # the real batch; needs a clean working tree
  python results_v2_g06/run_all.py --smoke    # tiny version into a scratch directory, one forced timeout
"""
import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
REGIMES = ('nonce-only', 'full-header')
HEADLINE_NQ = {1: 50, 2: 45, 3: 35, 4: 25}
SWEEP_NQ = {1: 25, 2: 30, 3: 20, 4: 15}
SWEEP_GAMMAS = [round(0.50 + 0.05 * i, 2) for i in range(11)]
HEADLINE_DAYS, SWEEP_DAYS, CONTROL_DAYS = 1_000_000, 100_000, 1_000_000
TIMEOUT_S = 3 * 3600
PROCESSES = 6
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
# Lines run.py prints as it enters each stage, latest stage last (keep in step with run.py's prints).
STAGES = [('Configuration', 'configuration'), ('Payoff matrices built', 'payoff matrices built'),
          ('After elimination', 'eliminated dominated strategies'), ('Lemke-Howson (stop_after', 'Lemke-Howson'),
          ('Lemke-Howson found', 'equilibria found'), ('Resuming: using saved equilibria', 'equilibria loaded'),
          ('Alice U =', 'expected payoffs'), ('Simulating', 'simulation'), ('Control: simulating', 'simulation'),
          ('Metadata written', 'finished')]


@dataclass
class Config:
    name: str
    step: str
    args: list
    out_dir: Path
    meta_name: str                     # the meta JSON run.py writes in out_dir
    timeout_s: float | None = TIMEOUT_S
    status: str = 'pending'
    stage: str = ''
    started: str = ''
    finished: str = ''
    elapsed_s: float | None = None
    meta: dict | None = None

    @property
    def argv(self) -> list[str]:
        # Output directories inside the repo are passed relative to it (run.py runs from the repo root).
        return [a.relative_to(REPO).as_posix() if isinstance(a, Path) and a.is_relative_to(REPO) else str(a)
                for a in self.args]

    @property
    def command(self) -> str:
        return 'python run.py ' + ' '.join(shlex.quote(a) for a in self.argv)


def plan(root: Path, smoke: bool) -> list[Config]:
    headline_nq = {c: 4 for c in HEADLINE_NQ} if smoke else HEADLINE_NQ
    sweep_nq = {c: 4 for c in SWEEP_NQ} if smoke else SWEEP_NQ
    gammas = [0.6, 1.0] if smoke else SWEEP_GAMMAS
    days = (24, 24, 24) if smoke else (HEADLINE_DAYS, SWEEP_DAYS, CONTROL_DAYS)
    common = ['--processes', 2 if smoke else PROCESSES]

    def headline(c):
        return [Config(f'headline_c{c}_{r}', 'headline',
                       ['--regime', r, '-c', c, '--n-q', headline_nq[c], '--gamma', '0.60', '--num-simulations', days[0],
                        '--out-dir', root, *common], root, f'meta_c{c}_{r}.json') for r in REGIMES]

    def sweep(c):
        out = []
        for g in gammas:
            d = root / 'sweep' / f'g{g:.2f}'
            out.append(Config(f'sweep_c{c}_g{g:.2f}', 'sweep',
                              ['--regime', 'full-header', '-c', c, '--n-q', sweep_nq[c], '--gamma', f'{g:.2f}',
                               '--num-simulations', days[1], '--no-plot', '--out-dir', d, *common], d,
                              f'meta_c{c}_full-header.json'))
        return out

    second = root / 'c3_stop_after_2'
    return [
        *headline(1), *headline(2),
        *sweep(1), *sweep(2),
        Config('control', 'control', ['--regime', 'full-header', '--control', '--num-simulations', days[2],
                                      '--out-dir', root, *common], root, 'meta_control.json'),
        *headline(3), *headline(4),
        *sweep(3), *sweep(4),
        # Untimed, so last: a full-header second-equilibrium search that never ends blocks nothing else.
        *[Config(f'c3_stop_after_2_{r}', 'second equilibria',
                 ['--regime', r, '-c', 3, '--n-q', headline_nq[3], '--gamma', '0.60', '--stop-after', 2,
                  '--num-simulations', days[0],
                  '--out-dir', second, *common], second, f'meta_c3_{r}.json', timeout_s=None) for r in REGIMES],
    ]


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == 'nt':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def last_stage(log: Path) -> str:
    stage = ''
    for line in log.read_text(errors='replace').splitlines():
        for marker, name in STAGES:
            if marker in line:
                stage = name
    return stage


def run(cfg: Config, logs: Path) -> None:
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    log = logs / f'{cfg.name}.log'
    cfg.started = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'=== {cfg.name}  {cfg.started}  (limit {cfg.timeout_s or "none"} s)', flush=True)
    t0 = time.time()
    extra = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
    with open(log, 'w') as f:
        proc = subprocess.Popen([sys.executable, '-u', 'run.py', *cfg.argv], cwd=REPO,
                                stdout=f, stderr=subprocess.STDOUT, env=ENV, **extra)
        try:
            code = proc.wait(timeout=cfg.timeout_s)
            cfg.status = 'done' if code == 0 else f'failed (exit code {code})'
        except subprocess.TimeoutExpired:
            kill_tree(proc)
            cfg.status = 'timed out'
    cfg.elapsed_s = time.time() - t0
    cfg.finished = time.strftime('%Y-%m-%d %H:%M:%S')
    cfg.stage = last_stage(log)
    if cfg.status != 'done':
        with open(log, 'a') as f:
            f.write(f'\n[run_all] {cfg.status} after {cfg.elapsed_s:.0f} s; last stage reached: {cfg.stage}\n')
    meta_path = cfg.out_dir / cfg.meta_name
    cfg.meta = json.loads(meta_path.read_text()) if cfg.status == 'done' and meta_path.exists() else None
    print(f'    {cfg.status} at {cfg.finished} after {cfg.elapsed_s:.0f} s (stage: {cfg.stage})', flush=True)


def has_zero_measurement(eq: dict) -> bool:
    return any(0 in s['strategy'] for player in ('alice', 'bob') for s in eq[f'{player}_support'])


def write_readme(root: Path, configs: list[Config], batch_started: str, batch_finished: str, commit: str) -> None:
    done = sum(c.status != 'pending' for c in configs)
    lines = [
        '# Results v2, first-finder fork rule (headline gamma_S = 0.6)', '',
        'Produced by `results_v2_g06/run_all.py` (ticket `.scratch/revision-v2/issues/01-first-finder-gamma.md`). '
        'Equilibria are Gambit `lcp_solve(rational=True)`, first equilibrium found. Commands run from the repo root.', '',
        f'- Commit: `{commit}`',
        f'- Batch started: {batch_started}',
        f'- Batch finished: {batch_finished or "still running (or the driver was stopped)"}',
        f'- Progress: {done} of {len(configs)} configurations attempted; '
        f'{sum(c.status == "done" for c in configs)} done, {sum(c.status == "timed out" for c in configs)} timed out, '
        f'{sum(c.status.startswith("failed") for c in configs)} failed.',
        f'- Wall-clock limit per configuration: {TIMEOUT_S // 3600} h (none for the c = 3 second-equilibrium runs).', '',
        '## Configurations', '',
        '| # | configuration | step | status | last stage | started | elapsed (s) | output | command |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for i, c in enumerate(configs, 1):
        elapsed = '' if c.elapsed_s is None else f'{c.elapsed_s:.0f}'
        out = os.path.relpath(c.out_dir, root).replace('\\', '/')
        lines.append(f'| {i} | {c.name} | {c.step} | {c.status} | {c.stage} | {c.started} | {elapsed} | `{out}` | `{c.command}` |')

    lines += ['', '## Equilibria', '',
              'A measurement at iteration 0 is wasted; equilibria that contain one are flagged.', '',
              '| configuration | eq | after elimination | Alice U | Bob U | E[first]/κ (Alice, Bob) | supports (A, B) | symmetric | zero measurement | P95 | P_det |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
    for c in configs:
        if c.meta:
            m = c.meta
            for e in m.get('equilibria', []):
                s = e.get('stats') or {}
                dim = ' × '.join(map(str, m['dimension_after_elimination']))
                lines.append(
                    f"| {c.name} | {e['label'] or 'eq1'} | {dim} | {e['alice_ep']:.5f} | {e['bob_ep']:.5f} | "
                    f"{e['alice_first_measurement']:.4f}, {e['bob_first_measurement']:.4f} | "
                    f"{len(e['alice_support'])}, {len(e['bob_support'])} | {e['symmetric']} | "
                    f"{'**yes**' if has_zero_measurement(e) else 'no'} | "
                    f"{s.get('p95_stale_rate', float('nan')):.6f} | {s.get('detection_prob_05', float('nan')):.6f} |")
    control = next((c for c in configs if c.step == 'control' and c.meta), None)
    if control:
        s = control.meta['stats']
        lines += ['', '## No-quantum-miner control', '',
                  f"{s['num_days']:,} days: mean p_stale {s['mean_stale_rate']:.6f} (model 0.0024), "
                  f"P_det {s['detection_prob_05']:.6f} [{s['detection_prob_05_ci'][0]:.6f}, "
                  f"{s['detection_prob_05_ci'][1]:.6f}] (expected about 0.047)."]
    lines += ['', 'The sweep table is `sweep/stale_rate_vs_gamma.csv` (plots in `sweep/images/`); '
              'the summary tables are `tables.md`. Per-configuration logs are in `logs/`.', '']
    (root / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


def collect(root: Path, logs: Path) -> None:
    for script, args, out in (('sweep_gamma.py', [root / 'sweep'], logs / 'sweep_gamma.log'),
                              (HERE / 'make_tables.py', [root], None)):
        result = subprocess.run([sys.executable, str(REPO / script), *map(str, args)], cwd=REPO,
                                capture_output=True, text=True, encoding='utf-8', env=ENV)
        if out:
            out.write_text(result.stdout + result.stderr)
        else:
            (root / 'tables.md').write_text(result.stdout, encoding='utf-8')
        if result.returncode != 0:
            print(f'    {Path(script).name} failed: {result.stderr[-500:]}', flush=True)


def tracked_changes() -> str:
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=REPO, capture_output=True, text=True).stdout
    return '\n'.join(line for line in status.splitlines() if not line.startswith('??'))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--smoke', metavar='DIR', type=Path, nargs='?', const=None, default=False,
                        help='Tiny batch into DIR (default: a temp directory) with one forced timeout')
    args = parser.parse_args()
    smoke = args.smoke is not False
    if smoke:
        import tempfile
        root = (args.smoke or Path(tempfile.mkdtemp(prefix='run_all_smoke_'))).resolve()
    else:
        root = HERE
        if tracked_changes():
            sys.exit(f'Tracked files have uncommitted changes; commit first so the meta commit matches:\n{tracked_changes()}')
    logs = root / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    configs = plan(root, smoke)
    if smoke:
        configs[0].timeout_s = 2          # forced timeout: headline c = 1 nonce-only

    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True, text=True).stdout.strip()
    started = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'Batch started {started} at commit {commit}; output in {root}', flush=True)
    write_readme(root, configs, started, '', commit)
    for i, cfg in enumerate(configs):
        try:
            run(cfg, logs)
        except Exception as exc:          # the driver itself must keep going
            cfg.status = f'failed ({type(exc).__name__}: {exc})'
            print(f'    {cfg.status}', flush=True)
        if cfg.step == 'sweep' and i + 1 < len(configs) and configs[i + 1].step != 'sweep':
            collect(root, logs)
        write_readme(root, configs, started, '', commit)
    collect(root, logs)
    finished = time.strftime('%Y-%m-%d %H:%M:%S')
    write_readme(root, configs, started, finished, commit)
    print(f'Batch finished {finished}', flush=True)


if __name__ == '__main__':
    main()
