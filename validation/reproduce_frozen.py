"""Re-run the exact archived validation plan in a fresh directory (Linux recommended)."""
import argparse, hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path

def digest(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def unpack(p,d):
    d.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(p) as z:
        for name in z.namelist():
            if not (d/name).resolve().is_relative_to(d.resolve()): raise ValueError('Unsafe archive path')
        z.extractall(d)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--general',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=2);p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    root=a.out.resolve();root.mkdir(parents=True,exist_ok=False)
    audit=root/'audit';unpack(Path(__file__).resolve().parent/'audit/final_validation.zip',audit)
    plan=audit/'results/frozen_plan.json';cfg=json.loads(plan.read_text());source=root/'source';unpack(audit/'frozen_source.zip',source)
    for k,v in cfg['code_sha256'].items():
        if digest(source/k)!=v: raise ValueError('Frozen source hash mismatch: '+k)
    for k,archive in [('general',a.general),('fixture',a.fixture)]:
        if digest(archive)!=cfg['data_sha256'][k]: raise ValueError('Data hash mismatch: '+k)
    print('All frozen source and data fingerprints verified',flush=True)
    if a.verify_only:return
    general=root/'general';fixture=root/'fixture';unpack(a.general,general);unpack(a.fixture,fixture)
    # Locate roots robustly, irrespective of the archive's top-level directory.
    jpeg=next(x.parent for x in general.rglob('manifest.csv') if x.parent.name=='JPEG')
    vox=next(x.parent for x in general.rglob('manifest_truth.csv') if x.parent.name=='VOX')
    fixture=next(x.parent for x in fixture.rglob('manifest.csv') if (x.parent/'sections.csv').exists())
    env=os.environ.copy();env.update(PYTHONPATH=str(source/'src'),MPLBACKEND='Agg',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    results=root/'results';results.mkdir()
    for kind,split,data,candidate in [('jpeg','development',jpeg,True),('vox','development',vox,True),('jpeg','test',jpeg,True),('vox','test',vox,True),('fixture','test',fixture,False)]:
        target=results/(('dev' if split=='development' else 'test')+'_'+kind)
        cmd=[sys.executable,'validation/run_local_parallel.py','--data',str(data),'--out',str(target),'--kind',kind,'--split',split,'--workers',str(a.workers)]
        if candidate:cmd+=['--candidate']
        if split=='test':cmd+=['--plan',str(plan)]
        subprocess.run(cmd,cwd=source,env=env,check=True)
    subprocess.run([sys.executable,str(audit/'summarize.py'),str(results),str(audit/'development_github_release_v1_results.zip')],env=env,check=True)
if __name__=='__main__':main()
