"""Curriculum for Cloud Change Control. Each phaseNN_* package defines PHASE."""

from pce.lesson import collect

PHASES = collect(__name__, __path__, "phase", "PHASE")
