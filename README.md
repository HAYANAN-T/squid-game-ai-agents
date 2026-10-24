# The Five Games — reproducible 2D agent-policy simulator

This repository contains **working simulation code only**: six transparent Python policies, five scored rounds, a browser-based 2D game-world replay, deterministic result records, statistical stress tests, and automated checks. It deliberately contains no Medium article or image assets. **No commercial LLM calls occur.**

## Quick start

Python 3.10+, no network or tokens required. The core simulator uses only the Python standard library.

```bash
python arena.py --seed 42 --tournaments 250 --output results
python stress_tests.py --seeds 500 --output results
python build_world.py --featured results/featured.json --output world/squid_game_2d_world.html
python -m unittest discover -s tests -v
```

Open `world/squid_game_2d_world.html` in a normal browser. The five scene tabs, Play/Pause, step slider, and action inspector all use the saved decisions in `results/featured.json`.

For research figures and actual browser screenshot captures, install the optional development dependencies:

```bash
python -m pip install matplotlib==3.10.8 playwright==1.57.0
python -m playwright install chromium
python plot_results.py --results results --out ../article_assets
python plot_stress.py --input results/poisoned_memory.csv --output ../article_assets/fig_memory_poisoning_white.png
python capture_screenshots.py --world world/squid_game_2d_world.html --output ../article_assets
```

If Chromium is already installed systemwide at `/usr/bin/chromium`, the screenshot script uses it. The article's captures were made with a real Chromium render, not synthetic image generation.

## What the five games test

1. **Red Light:** cooperative cancellation polling in logical *ticks*; not physical reaction milliseconds.
2. **Dalgona:** exact serialization and semantic value correctness. Regular JSON parsers allow whitespace, but this round deliberately requires exact bytes.
3. **Tug of War:** evidence-based debate against a small, predefined truth table. The referee is not an LLM.
4. **Marbles:** incomplete-information bargaining with private reservation thresholds and up to four offers.
5. **Glass Bridge:** decisions from a noisy clue and optional verified earlier failures. Twenty repeated panels, *not* literal elimination after one wrong tile.

`stress_tests.py` corrupts public failure reports at six rates and compares memory ON/OFF using paired environments, fixed clue draws, and 500 seeded worlds per configuration.

## Saved data and interpretation

- `results/featured.json`: detailed seed-42 event log with observations, actions, checks and outcomes.
- `results/tournaments.csv`: one row per seed; 250 tournaments.
- `results/rounds.csv`: 5 elimination stages per seed, surviving policies only.
- `results/bridge_ablation.csv`: verified-failure memory ON/OFF ablation.
- `results/poisoned_memory.csv`: 500-world corrupted-feedback paired comparisons.
- `results/summary.json`, `results/memory_noise_summary.json`: machine-readable summaries.

The one-seed featured tournament is storytelling, **not statistical proof of real model superiority**. Model 'thinking time' is not observed; measured Python microseconds record this algorithm's execution overhead and will change by hardware. Polling ticks are logical, with no valid direct conversion to wall-clock time.

The code generates screenshots *outside the repository* in the article-assets folder. Neither third-party photography nor generated figures belong in this code-only repository.

## No fabricated thought traces

The viewer shows deterministic event explanations authored by game rules. There is no chain-of-thought capture and no access to private reasoning in ChatGPT, Claude, Gemini, or any other service.

## Provenance

For genuine language-model comparisons, adapt an actual tool-calling API adapter, log provider/model/version, exact prompts, token budgets, costs, API timing, tool calls, and independently verified scores. **Do not relabel the six built-in policies as commercial models.**

MIT License; check `LICENSE`.
