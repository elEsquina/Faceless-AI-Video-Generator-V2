FROM ai-video-sandbox-blender:latest
ARG BLENDER_VERSION=4.5.16
ARG BLENDER_SHA256=23432b064977908beb1ab4b7f32f024e7331105c875c187dce002aff84b10c11
# Official LTS binary includes RTX 50x0 support; reuse the tested CPU image's libraries.
RUN python3 - <<'PY'
import hashlib,os,pathlib,tarfile,urllib.request
version=os.environ['BLENDER_VERSION']
archive=pathlib.Path('/tmp/blender.tar.xz')
url=f'https://download.blender.org/release/Blender4.5/blender-{version}-linux-x64.tar.xz'
hash=hashlib.sha256()
with urllib.request.urlopen(url) as source,archive.open('wb') as target:
    while chunk:=source.read(1024*1024):
        hash.update(chunk);target.write(chunk)
if hash.hexdigest()!=os.environ['BLENDER_SHA256']:
    raise RuntimeError('Official Blender archive checksum mismatch')
with tarfile.open(archive,'r:xz') as package:package.extractall('/opt',filter='data')
pathlib.Path(f'/opt/blender-{version}-linux-x64').rename('/opt/blender')
archive.unlink()
PY
ENV PATH="/opt/blender:${PATH}"
RUN apt-get update && apt-get install -y --no-install-recommends libsm6 libxrender1 libxi6 libxkbcommon0 libxfixes3 libxxf86vm1 libxrandr2 \
 && rm -rf /var/lib/apt/lists/*
RUN blender -b --version
