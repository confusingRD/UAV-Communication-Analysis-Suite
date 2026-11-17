"""Recreate synthetic examples. All scenarios are fixtures, not mission forecasts."""
from datetime import datetime, timedelta, timezone
import json
from math import sin, cos, sqrt
from pathlib import Path

from cubesat_link import (SPHERE, GroundStation, SatelliteState, NeutralProfile,
                          trace_spherical)


def main():
    root = Path(__file__).resolve().parent
    epoch = datetime(2026,11,14,tzinfo=timezone.utc)
    station = dict(lat_deg=0,lon_deg=0,altitude_m=0,min_elevation_deg=10)
    earth = dict(model='sphere',radius_m=6371000)
    state = dict(position_m=[6871000,0,0],frame='ECEF',epoch_utc='2026-11-14T00:00:00Z')
    radio = dict(tx_power_dbm=30,tx_gain_dbi=2,rx_gain_dbi=12,tx_pointing_loss_db=0,
                 rx_pointing_loss_db=0,cable_loss_db=2,receiver_threshold_dbm=-120,
                 receiver_mode='Synthetic fixed threshold example; no modulation/rate assertion',
                 antenna_basis='Synthetic ideal tracking and boresight gains')
    base = dict(schema_version='1.0',operation='evaluate_link',earth=earth,station=station,
                state=state,frequency_hz=2.4e9,radio=radio,
                polarization=dict(tx='circular',rx='circular',circular_match=True))
    metadata = dict(source='Synthetic example: homogeneous finite electron column',version='fixture-1',
                    epoch_utc=state['epoch_utc'],temporal_kind='synthetic',
                    applicability='Synthetic radial ground-to-500-km endpoint only; not IRI or space weather',
                    units=dict(distance_m='m',density_per_m3='el/m3',b_parallel_t='T'))
    electrons = dict(kind='path',metadata=metadata,
                     binding=dict(station=station,state=state,earth=earth,path_kind='spherical_refracted',path_length_m=500000),
                     data=dict(distance_m=[0,100000,300000,500000],density_per_m3=[0,0,1e12,5e11],
                               b_parallel_t=[5e-5]*4,source='Synthetic example, four samples along radial ray'))
    cube = dict(base,neutral=dict(kind='p834_reference'),electrons=electrons)
    ideal = dict(base,vacuum=True)
    # Bounded UAV table is deliberately non-vacuum at 11 km. No false n(top)=1.
    uav_station = dict(station,min_elevation_deg=0)
    uav_state = dict(state,position_m=[6377000,0,0])
    profile = dict(height_m=[0,11000],refractive_index=[1.0003,1.0001],
                   frequency_range_hz=[1e9,3e9],gamma_db_per_km=[0.02,0.01],
                   gas_frequency_hz=2.4e9,gas_source='Synthetic gamma table, NOT P.676',
                   source='Synthetic UAV refractivity table, NOT local weather',outside='unavailable')
    neutral_meta = dict(source='Synthetic example neutral and gas table',version='fixture-1',
                        epoch_utc=state['epoch_utc'],temporal_kind='synthetic',
                        applicability='Horizontally homogeneous 0-11 km ONLY; n valid 1-3 GHz, gas at 2.4 GHz only',
                        units=dict(height_m='m',refractive_index='1',gamma_db_per_km='dB/km'))
    uav = dict(base,station=uav_station,state=uav_state,
               neutral=dict(kind='table',profile=profile,metadata=neutral_meta))
    radius = 6871000
    omega = sqrt(3.986004418e14/radius**3)-7.292115e-5
    states = [dict(position_m=[radius*cos(omega*(t-600)),radius*sin(omega*(t-600)),0],
                   frame='ECEF',epoch_utc=(epoch+timedelta(seconds=t)).isoformat().replace('+00:00','Z'))
              for t in range(0,1201,10)]
    windows = dict(schema_version='1.0',operation='contact_windows',earth=earth,station=station,
                   states=states,max_gap_s=60,mode='geometric')
    for name,data in [('cubesat',cube),('cubesat_ideal',ideal),('uav',uav),('pass',windows)]:
        (root/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
