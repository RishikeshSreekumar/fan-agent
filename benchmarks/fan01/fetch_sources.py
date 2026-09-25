"""Fetch only the pinned aerodynamic files; verify bytes before extraction."""
from pathlib import Path
import json,hashlib,urllib.request,zipfile
ROOT=Path(__file__).resolve().parent
for f in json.loads((ROOT/'source-manifest.json').read_text())['files']:
    path=ROOT/f['name']
    if path.exists(): data=path.read_bytes()
    else:
        with urllib.request.urlopen(f['url'],timeout=90) as response:data=response.read()
    if len(data)!=f['size_bytes'] or hashlib.sha256(data).hexdigest()!=f['sha256']:
        raise ValueError('Source checksum mismatch: '+f['name'])
    if not path.exists():path.write_bytes(data)
    if path.suffix=='.zip':
        destination=(ROOT/'extracted').resolve()
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                target=(destination/entry.filename).resolve()
                if not target.is_relative_to(destination) or (entry.external_attr>>16)&0o170000==0o120000:
                    raise ValueError('Unsafe archive member')
            archive.extractall(destination)
    print('Verified',f['name'])
