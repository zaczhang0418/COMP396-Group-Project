# -*- coding: utf-8 -*-
"""Coursework 3 archive alias for the final Team01 V3 strategy.

The assignment submission file remains ``team01.py``. This module gives the
archive branch a versioned strategy id so V3 evidence can be regenerated without
confusing it with the earlier Team01/V2 presubmission strategy.
"""

from strategies.team01 import TeamStrategy as _TeamStrategy


class Team01V3Strategy(_TeamStrategy):
    """Versioned wrapper around the final CA3 Team01 implementation."""

    pass
