"""Synthetic 6-km UAV using a bounded 0-11-km profile; missing losses stay unknown."""
from pathlib import Path
import json
from cubesat_link.interface import load_request, run_request

if __name__=='__main__':
    request = load_request(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))
    print(json.dumps(run_request(request),indent=2,allow_nan=False))
