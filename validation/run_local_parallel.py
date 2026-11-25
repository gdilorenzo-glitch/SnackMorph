"""Parallel execution of unchanged benchmark case functions; case-level audit files."""
import argparse,hashlib,json,platform,traceback,warnings
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from importlib.metadata import version,PackageNotFoundError
from types import SimpleNamespace
import cv2,pandas as pd
import run_benchmark as b
import run_fixture_benchmark as f

def fingerprint():
    return b.fingerprint()|{'validation/run_local_parallel.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'validation/run_fixture_benchmark.py':hashlib.sha256((b.ROOT/'validation/run_fixture_benchmark.py').read_bytes()).hexdigest()}
def job(args):
    kind,root,r,out,candidate=args;row=SimpleNamespace(**r);root=Path(root);out=Path(out);cv2.setNumThreads(1);ident=r.get('image_id',r.get('volume_id',r.get('case')));dest=out/ident;dest.mkdir(parents=True,exist_ok=True)
    try:
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')
            if kind=='jpeg':
                tr=pd.read_csv(root/'objects_truth.csv');pr=pd.read_csv(root/'profiles_truth.csv');rec,widths,log=b.jpeg_case(root,row,tr[tr.image_id==ident],pr[pr.image_id==ident],candidate=candidate);pd.DataFrame(widths).to_csv(dest/'widths.csv',index=False)
            elif kind=='vox':
                features=json.loads((root/'primitive_geometry.json').read_text());rec,log=b.voxel_case(root,row,[x for x in features if x['group']==row.group],candidate=candidate)
            else:
                tmp=dest/'input';tmp.mkdir(exist_ok=True);(tmp/ident).symlink_to(root/ident,target_is_directory=True);pd.DataFrame([r]).to_csv(tmp/'manifest.csv',index=False);sec=pd.read_csv(root/'sections.csv');sec[sec.case==ident].to_csv(tmp/'sections.csv',index=False);f.main(tmp,dest,row.split);log={'case':ident,'status':json.loads((dest/(ident+'.json')).read_text())['volume']['status']};rec=None
            if rec is not None:pd.DataFrame(rec).to_csv(dest/'metrics.csv',index=False)
            log['warnings']=[str(w.message) for w in ws]
    except Exception as e:log={'id':ident,'status':'failed','error':repr(e),'traceback':traceback.format_exc()}
    (dest/'log.json').write_text(json.dumps(log,indent=2,default=str));(dest/'DONE').touch();return ident,log['status']
def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--split',choices=['development','test'],required=True);p.add_argument('--kind',choices=['jpeg','vox','fixture'],required=True);p.add_argument('--candidate',action='store_true');p.add_argument('--plan',type=Path);p.add_argument('--workers',type=int,default=2);a=p.parse_args();a.data=a.data.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    if a.split=='test':
        assert a.plan;plan=json.loads(a.plan.read_text());assert plan['code_sha256']==fingerprint();assert plan['approved_for_execution_by']=='User delegated final validation; analyst selected criteria before test';assert plan['modes'][a.kind]==a.candidate;(a.out/'frozen_plan.json').write_text(a.plan.read_text())
    env=dict(python=platform.python_version(),platform=platform.platform(),kind=a.kind,split=a.split,candidate=a.candidate,code_sha256=fingerprint())
    for pkg in ['numpy','pandas','scipy','scikit-image','opencv-python-headless','scikit-learn','Pillow','matplotlib','statsmodels','pytest']:
        try:env[pkg]=version(pkg)
        except PackageNotFoundError:env[pkg]='not installed'
    (a.out/'environment.json').write_text(json.dumps(env,indent=2));m=pd.read_csv(a.data/('manifest_truth.csv' if a.kind=='vox' else 'manifest.csv'));m=m[m.split==a.split];jobs=[(a.kind,str(a.data),r,str(a.out),a.candidate) for r in m.to_dict('records')]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i,fu in enumerate(as_completed([ex.submit(job,j) for j in jobs]),1):print(i,len(jobs),fu.result(),flush=True)
    for file in (['volume_metrics.csv','slice_metrics.csv'] if a.kind=='fixture' else ['metrics.csv','widths.csv']):
        dfs=[pd.read_csv(path) for path in sorted(a.out.glob('*/'+file))];
        if dfs:pd.concat(dfs,ignore_index=True).to_csv(a.out/file,index=False)
    pd.DataFrame([json.loads(p.read_text()) for p in sorted(a.out.glob('*/log.json'))]).to_csv(a.out/'log.csv',index=False)
if __name__=='__main__':main()
