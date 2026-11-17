"""UAV-CAS Phase 1 scientific foundations.

The package deliberately contains no GUI imports and no Phase 2 ray solver.
"""

from .atmosphere.isa import AtmosphereState, AltitudeKind, standard_atmosphere
from .atmosphere.refractivity import RefractivityResult, radio_refractivity
from .link_budget import calculate_reference_link_budget

__all__ = [
    "AltitudeKind",
    "AtmosphereState",
    "RefractivityResult",
    "calculate_reference_link_budget",
    "radio_refractivity",
    "standard_atmosphere",
]

__version__ = "0.1.0"

