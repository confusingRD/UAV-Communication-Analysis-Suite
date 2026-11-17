"""Synthetic 500-km CubeSat, P.834 reference neutral model and finite electron path."""
from pathlib import Path
import json
from cubesat_link.interface import load_request, run_request

if __name__=='__main__':
    request = load_request(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))
    print(json.dumps(run_request(request),indent=2,allow_nan=False))
