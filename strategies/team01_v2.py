# -*- coding: utf-8 -*-
"""Coursework 2 archive alias for the Team01 V2 presubmission strategy.

The historical implementation remains ``team01.py``. This module gives the
archive branch a versioned strategy id that matches the V1/V3 summary-branch
naming convention.
"""

from strategies.team01 import TeamStrategy as _TeamStrategy


class Team01V2Strategy(_TeamStrategy):
    """Versioned wrapper around the CA2 Team01 V2 presubmission strategy."""

    pass
