"""Allowlist packaging: two handoff ZIPs, per-file manifest and SHA256SUMS."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2.0'
PREFIX = f'cubesat-link-{VERSION}'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    common = {'README.md':ROOT/'README.md'}
    for folder in ('docs','examples','tests','schemas'):
        for path in (ROOT/folder).rglob('*'):
            if path.is_file() and path.suffix in ('.md','.json','.py') and '__pycache__' not in path.parts:
                common[path.relative_to(ROOT).as_posix()] = path
    wheel = f'dist/cubesat_link-{VERSION}-py3-none-any.whl'
    common[wheel] = ROOT/wheel
    for required in ('docs/RELEASE.md','docs/verification.json','schemas/request.schema.json',wheel):
        assert required in common and common[required].is_file(), required
    full = dict(common)
    for folder in ('cubesat_link','scripts'):
        for path in (ROOT/folder).rglob('*'):
            if path.is_file() and path.suffix in ('.py','.json') and '__pycache__' not in path.parts:
                full[path.relative_to(ROOT).as_posix()] = path
    full['pyproject.toml'] = ROOT/'pyproject.toml'
    for name in ('api.py','budget.py','geometry.py','ionosphere.py','neutral.py','app.py','config.py',
                 'main.py','plots.py','raytrace.py','service.py','requirements.txt','run_gui.bat','run_gui.sh'):
        full['legacy/'+name] = ROOT/name
    products = [ROOT/wheel]
    for kind,files in [('source',full),('integration',common)]:
        target = ROOT/'dist'/f'{PREFIX}-{kind}.zip'
        manifest = ''.join(f'{digest(path.read_bytes())}  {name}\n' for name,path in sorted(files.items()))
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for name,path in sorted(files.items()):
                archive.write(path,PREFIX+'/'+name)
            archive.writestr(PREFIX+'/MANIFEST.sha256',manifest)
        with zipfile.ZipFile(target) as archive:
            assert archive.testzip() is None
            for line in manifest.splitlines():
                expected,name = line.split('  ',1)
                assert digest(archive.read(PREFIX+'/'+name))==expected
        products.append(target)
        print(f'{target.name}: {len(files)} payload files; CRC and SHA256 manifest verified')
    sums = ''.join(f'{digest(path.read_bytes())}  {path.name}\n' for path in products)
    (ROOT/'dist/SHA256SUMS.txt').write_text(sums,encoding='ascii')
    print(sums)


if __name__=='__main__':
    main()
