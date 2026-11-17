"""Reproducible comparisons against published equations (not measured validation)."""
from math import cos, sin, radians, log10
from cubesat_link import *


def main():
    for frequency in (868e6,915e6,2.4e9):
        actual=fspl_db(500000,frequency)
        rounded=32.4+20*log10(frequency/1e6)+20*log10(500)
        print(f'P525 f={frequency:g} Hz d=500000 m: exact={actual:.12f} dB; Eq6={rounded:.12f}; delta={actual-rounded:.12f}')
    tec=SlantTEC(1e17,500000,'validation 10 TECU; B_parallel=50 uT',5e12)
    for frequency in (868e6,915e6,1e9,2.4e9):
        result=ionospheric_effects(frequency,tec)
        p531_delay=1.345e-7*1e17/frequency**2
        print(f'P531 f={frequency:g} Hz: delay={result["group_delay"].value*1e9:.12f} ns; published rounded={p531_delay*1e9:.12f}; Faraday={result["faraday_rotation"].value:.12f} rad')
    earth=Earth(6370000,0)  # P.834 reference radius
    radius=earth.semi_major_m+500000
    state=SatelliteState((radius*cos(radians(20)),radius*sin(radians(20)),0),'ECEF')
    ray=trace_spherical(GroundStation(0,0,0),state,915e6,p834_reference_profile(),earth)
    theta=ray.apparent_elevation_deg
    approximation=1/(1.314+0.6437*theta+0.02869*theta**2)
    print(f'P834 R=6370 km, h_station=0, h_sat=500 km, central angle=20 deg: launch={theta:.12f} deg; bend={ray.bending_deg:.12f} deg; Eq9={approximation:.12f} deg; delta={ray.bending_deg-approximation:.12f} deg; endpoint residual={ray.endpoint_residual_rad:.3g} rad')


if __name__=='__main__': main()
