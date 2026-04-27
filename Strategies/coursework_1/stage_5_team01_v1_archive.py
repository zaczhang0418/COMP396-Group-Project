# -*- coding: utf-8 -*-
"""Coursework 1 archive alias for the initial Team01 V1 combo strategy.

The historical implementation remains ``stage_4_initial_combo_team01_v1.py``. This
module gives the archive branch a versioned Team01 strategy id that matches the
V2/V3 summary-branch naming convention.
"""

from Strategies.coursework_1.stage_4_initial_combo_team01_v1 import ComboTF01MR10Garch07V1 as _ComboV1


class Team01V1Strategy(_ComboV1):
    """Versioned wrapper around the original CA1 Team01 V1 combo."""

    pass
