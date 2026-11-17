"""Phase 1 conditional free-space reference link budget.

This module reuses the preserved cubesat_link P.525 implementation.  It does
not infer atmospheric absorption and does not establish ray-based coverage.
"""

from __future__ import annotations

from dataclasses import dataclass

from cubesat_link.budget import fspl_db as verified_fspl_db

from .models import LinkConfiguration
from .validation import nonnegative, positive


@dataclass(frozen=True)
class ReferenceLinkBudgetResult:
    direction: str
    transmitter_id: str
    receiver_id: str
    distance_m: float
    frequency_hz: float
    free_space_path_loss_db: float
    received_power_dbm: float
    raw_margin_db: float
    design_margin_db: float
    meets_required_margin: bool
    assumptions: tuple[str, ...]


def calculate_reference_link_budget(
    configuration: LinkConfiguration,
    distance_m: float,
    *,
    other_verified_loss_db: float = 0.0,
) -> ReferenceLinkBudgetResult:
    """Calculate a manually traceable FSPL ledger for one link direction."""

    distance = positive(distance_m, "distance_m")
    other_loss = nonnegative(other_verified_loss_db, "other_verified_loss_db")
    transmitter = configuration.transmitter
    receiver = configuration.receiver
    fspl = verified_fspl_db(distance, configuration.frequency_hz)
    received = (
        transmitter.tx_power_dbm
        - transmitter.tx_feeder_loss_db
        + transmitter.tx_gain_dbi
        + receiver.rx_gain_dbi
        - receiver.rx_feeder_loss_db
        - fspl
        - other_loss
    )
    raw_margin = received - receiver.receiver_sensitivity_dbm
    design_margin = raw_margin - configuration.required_fade_margin_db
    return ReferenceLinkBudgetResult(
        direction=configuration.direction.value,
        transmitter_id=transmitter.identifier,
        receiver_id=receiver.identifier,
        distance_m=distance,
        frequency_hz=configuration.frequency_hz,
        free_space_path_loss_db=fspl,
        received_power_dbm=received,
        raw_margin_db=raw_margin,
        design_margin_db=design_margin,
        meets_required_margin=design_margin >= 0.0,
        assumptions=(
            "ITU-R P.525 free-space spreading evaluated at the supplied distance",
            "independent TX/RX gains and feeder losses selected by link direction",
            "no unverified atmospheric absorption term",
            "conditional reference budget; not ray-based communication coverage",
        ),
    )

