"""Shared filesystem locations for paper asset generation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
FIGURES = PAPER / "figures"
DATA = PAPER / "data"
