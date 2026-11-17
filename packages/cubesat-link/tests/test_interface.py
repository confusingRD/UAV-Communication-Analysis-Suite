import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cubesat_link
from cubesat_link import run_request, load_request, InputError
from cubesat_link.interface import schema_document, validate_document

ROOT = Path(__file__).resolve().parents[1]


class InterfaceTests(unittest.TestCase):
    def call_cli(self,text=None,path=None):
        source = Path(cubesat_link.__file__).resolve().parent == ROOT/'cubesat_link'
        with tempfile.TemporaryDirectory() as tmp:
            command = [sys.executable]+([] if source else ['-I'])+['-m','cubesat_link']
            if path is not None:
                command.append(str(path))
            return subprocess.run(command,input=text,text=True,capture_output=True,
                                  cwd=ROOT if source else tmp,timeout=30)

    def test_all_examples_cli_api_equal_and_schema_valid(self):
        for name in ('uav','cubesat','cubesat_ideal','pass'):
            with self.subTest(name=name):
                path = ROOT/'examples'/(name+'.json')
                request = load_request(path.read_text(encoding='utf-8'))
                expected = run_request(request)
                cli = self.call_cli(path=path)
                self.assertEqual(cli.returncode,0,cli.stderr+cli.stdout)
                self.assertEqual(cli.stderr,'')
                self.assertEqual(json.loads(cli.stdout),expected)
                validate_document(expected,schema_document('response'))
        cube = run_request(load_request((ROOT/'examples/cubesat.json').read_text()))['result']
        self.assertEqual(cube['losses_db']['gas']['status'],'not_computable')
        self.assertIsNone(cube['budget']['margin_db']['value'])
        self.assertEqual(cube['ionosphere']['group_delay']['status'],'computed')
        self.assertEqual(cube['providers']['electrons']['status'],'computed')

    def test_stdin_and_error_codes(self):
        request = (ROOT/'examples/cubesat_ideal.json').read_text()
        self.assertEqual(self.call_cli(text=request).returncode,0)
        for text,code in [('{','INVALID_JSON'),('{"x":1,"x":2}','INVALID_JSON'),
                          ('{"x":NaN}','INVALID_JSON'),('[]','SCHEMA_ERROR'),
                          ('{"schema_version":"2.0"}','UNSUPPORTED_SCHEMA')]:
            cli = self.call_cli(text=text)
            self.assertEqual(cli.returncode,2)
            response = json.loads(cli.stdout)
            self.assertEqual(response['error']['code'],code)
            validate_document(response,schema_document('response'))
        cli = self.call_cli(path=ROOT/'examples/does-not-exist.json')
        self.assertEqual(json.loads(cli.stdout)['error']['code'],'IO_ERROR')

    def test_strict_schema_and_semantic_validation(self):
        base = load_request((ROOT/'examples/cubesat_ideal.json').read_text())
        cases = []
        for key,value in [('frequency_hz',True),('frequency_hz',float('inf')),('frequency_hz',0),
                          ('vacuum','true'),('surprise',1)]:
            r = copy.deepcopy(base)
            r[key] = value
            cases.append(r)
        for field,value in [('frame','TEME'),('epoch_utc','2026-01-01T00:00:00'),
                            ('epoch_utc','2026-01-01T00:00:00+07:00'),('position_m',[0,1])]:
            r = copy.deepcopy(base)
            r['state'][field] = value
            cases.append(r)
        r = copy.deepcopy(base)
        r['supplied_losses'] = {'gas':dict(value=0,unit='dB',status='assumed',reason='duplicate vacuum gas')}
        cases.append(r)
        r = copy.deepcopy(base)
        r['neutral'] = {'kind':'p834_reference'}
        cases.append(r)
        for r in cases:
            with self.subTest(request=r),self.assertRaises(InputError):
                run_request(r)

    def test_no_units_clamp_or_implicit_earth(self):
        base = load_request((ROOT/'examples/cubesat_ideal.json').read_text())
        del base['earth']
        with self.assertRaises(InputError):
            run_request(base)
        base = load_request((ROOT/'examples/uav.json').read_text())
        base['neutral']['metadata']['units']['height_m'] = 'km'
        with self.assertRaises(InputError):
            run_request(base)


if __name__=='__main__':
    unittest.main()
