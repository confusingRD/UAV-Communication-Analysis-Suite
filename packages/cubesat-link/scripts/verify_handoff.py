"""Read-only archive checks plus isolated execution after safe temporary extraction."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'cubesat-link-0.2.0'


def main():
    forbidden = {'.venv','__pycache__','build','node_modules','.release-check','.git'}
    evidence = {'release':'0.2.0','archives':{}}
    for kind in ('source','integration'):
        path = ROOT/'dist'/f'{PREFIX}-{kind}.zip'
        with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory(prefix='cubesat-handoff-') as tmp:
            assert archive.testzip() is None
            for name in archive.namelist():
                p = PurePosixPath(name)
                assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
                assert p.parts[0]==PREFIX and not (set(p.parts)&forbidden)
                assert p.suffix not in ('.pyc','.log')
            manifest = archive.read(PREFIX+'/MANIFEST.sha256').decode('ascii')
            names = set()
            for line in manifest.splitlines():
                expected,name = line.split('  ',1)
                names.add(PREFIX+'/'+name)
                assert hashlib.sha256(archive.read(PREFIX+'/'+name)).hexdigest()==expected
            assert names|{PREFIX+'/MANIFEST.sha256'} == set(archive.namelist())
            archive.extractall(tmp)
            root = Path(tmp)/PREFIX
            # Force installed wheel even for full-source handoff; independent of cwd/PYTHONPATH.
            tests = subprocess.run([sys.executable,'-I','-m','unittest','discover','-s',str(root/'tests'),'-v'],
                                   cwd=tmp,capture_output=True,text=True,timeout=120)
            assert tests.returncode==0, tests.stderr
            cli = subprocess.run([sys.executable,'-I','-m','cubesat_link',str(root/'examples/cubesat.json')],
                                 cwd=tmp,capture_output=True,text=True,timeout=30)
            assert cli.returncode==0 and json.loads(cli.stdout)['ok']
            evidence['archives'][path.name] = {
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'crc':'passed','manifest':'passed','safe_paths_and_exclusions':'passed',
                'extracted_tests_exit_code':tests.returncode,'extracted_cli_exit_code':cli.returncode}
            print(f'{path.name}: safe paths, exclusions, manifest, extracted tests and CLI passed')
    (ROOT/'dist/handoff-verification.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
