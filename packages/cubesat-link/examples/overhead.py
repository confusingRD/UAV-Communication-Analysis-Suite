"""Synthetic ideal-vacuum demonstration, not a measured radio/real atmosphere."""
import json
from datetime import datetime, timezone
from cubesat_link import GroundStation, SatelliteState, Radio, Polarization, evaluate_link


def main():
    station=GroundStation(lat_deg=0,lon_deg=0,altitude_m=0,min_elevation_deg=10)
    satellite=SatelliteState((6878137,0,0),frame="ECEF",
                             epoch_utc=datetime(2026,11,14,tzinfo=timezone.utc))
    radio=Radio(tx_power_dbm=30,tx_gain_dbi=2,rx_gain_dbi=12,
                tx_pointing_loss_db=0,rx_pointing_loss_db=0,cable_loss_db=2,
                receiver_threshold_dbm=-120,receiver_mode="Synthetic fixed mode for example only",
                antenna_basis="Ideal tracking, both boresights aligned")
    result=evaluate_link(station,satellite,frequency_hz=915e6,radio=radio,
                         polarization=Polarization("linear","linear",alignment_rad=0),vacuum=True)
    print(json.dumps(result.to_dict(),indent=2,allow_nan=False))


if __name__=='__main__': main()
