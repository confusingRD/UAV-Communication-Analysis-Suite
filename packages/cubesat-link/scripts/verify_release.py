"""Run with the CLEAN environment's Python -I after installing the wheel.

No network; verifies installed origin, wheel bytes, all tests, CLI and examples.
Writes compact verification evidence and reproducible example responses, not logs.
"""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    import cubesat_link
    from cubesat_link.interface import load_request, run_request, schema_document, validate_document
    origin = Path(cubesat_link.__file__).resolve()
    if 'site-packages' not in origin.parts or origin.parent == ROOT/'cubesat_link':
        raise RuntimeError('Verification must use the installed wheel, not repository source')
    assert cubesat_link.__version__ == '0.2.0'
    distribution = importlib.metadata.distribution('cubesat-link')
    assert not distribution.requires, distribution.requires
    wheel = ROOT/'dist/cubesat_link-0.2.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as archive:
        assert archive.testzip() is None
        for source in (ROOT/'cubesat_link').iterdir():
            if source.suffix in ('.py','.json'):
                assert archive.read('cubesat_link/'+source.name) == source.read_bytes(), source
        assert all(name.startswith(('cubesat_link/','cubesat_link-0.2.0.dist-info/'))
                   for name in archive.namelist())
    results = {}
    with tempfile.TemporaryDirectory(prefix='cubesat-wheel-verify-') as work:
        def run(args,stdin=None):
            result = subprocess.run(args,input=stdin,cwd=work,text=True,capture_output=True,timeout=120)
            if result.returncode:
                raise RuntimeError(f'Failed {args}:\n{result.stdout}\n{result.stderr}')
            return result
        tests = run([sys.executable,'-I','-m','unittest','discover','-s',str(ROOT/'tests'),'-v'])
        match = re.search(r'Ran (\d+) tests',tests.stderr)
        assert match and '\nOK' in tests.stderr, tests.stderr
        results['tests'] = {'count':int(match[1]),'failures':0,'errors':0,'isolated':True}
        for name in ('uav','cubesat','cubesat_ideal','pass'):
            input_path = ROOT/'examples'/f'{name}.json'
            request = load_request(input_path.read_text(encoding='utf-8'))
            response = run_request(request)
            validate_document(response,schema_document('response'))
            actual = run([sys.executable,'-I','-m','cubesat_link',str(input_path)])
            assert not actual.stderr
            assert json.loads(actual.stdout) == response
            results[name] = 'API/CLI equal; request/response validated'
            (ROOT/'examples'/f'{name}.output.json').write_text(json.dumps(response,indent=2)+'\n',encoding='utf-8')
        for name in ('uav.py','cubesat.py','pass_demo.py','overhead.py','validation.py'):
            run([sys.executable,'-I',str(ROOT/'examples'/name)])
        results['python_examples'] = ['uav.py','cubesat.py','pass_demo.py','overhead.py','validation.py']
        console = Path(sys.executable).with_name('cubesat-link.exe' if sys.platform=='win32' else 'cubesat-link')
        request = (ROOT/'examples/cubesat_ideal.json').read_text(encoding='utf-8')
        actual = run([str(console),'-'],request)
        assert json.loads(actual.stdout)==run_request(load_request(request))
        results['console_entry_point'] = 'passed, including stdin'
        run([sys.executable,'-I','-m','pip','check'])
    results.update(release='0.2.0',python=sys.version,installed_origin=str(origin),
                   runtime_dependencies=[],wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
                   wheel_source_bytes_match=True)
    (ROOT/'docs/verification.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
