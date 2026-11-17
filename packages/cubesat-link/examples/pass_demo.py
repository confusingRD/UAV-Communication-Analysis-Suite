"""Synthetic equatorial circular pass: Earth rotation included, no TLE forecast.

mu=3.986004418e14 m3/s2 and Earth rotation=7.292115e-5 rad/s are WGS-84
defining constants (NGA.STND.0036). Radius 6371 km and altitude 500 km are
explicit scenario assumptions. No drag, J2, EOP, terrain or real spacecraft.
"""
from pathlib import Path
import json
from cubesat_link.interface import load_request, run_request


def main():
    request = load_request(Path(__file__).with_name('pass.json').read_text(encoding='utf-8'))
    result = run_request(request)
    samples = []
    for index in (0,60,120):
        state = request['states'][index]
        single = dict(schema_version='1.0',operation='evaluate_link',earth=request['earth'],
                      station=request['station'],state=state,frequency_hz=2.4e9,vacuum=True)
        link = run_request(single)['result']
        samples.append(dict(epoch_utc=state['epoch_utc'],geometric_visible=link['geometry']['geometric_visible'],
                            path_available=link['path_available']))
    print(json.dumps(dict(scenario='synthetic example; geometric windows only',
                         windows=result['result']['windows'],samples=samples),indent=2))


if __name__=='__main__':
    main()
