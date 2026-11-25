import argparse, json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description='SnackMorph research prototype; review outputs before scientific use')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('stats'); a.add_argument('data'); a.add_argument('output')
    a=sub.add_parser('ct-compare'); a.add_argument('csv'); a.add_argument('output')
    a=sub.add_parser('jpeg'); a.add_argument('image'); a.add_argument('calibration'); a.add_argument('output'); a.add_argument('--photo-key',required=True); a.add_argument('--lot',required=True); a.add_argument('--day',type=int,choices=[0,15,30],required=True); a.add_argument('--rows',type=int,required=True); a.add_argument('--crop',type=int,nargs=4); a.add_argument('--width-method',choices=['legacy','subpixel'],default='legacy',help='Diameter estimator; legacy preserves historical results')
    a=sub.add_parser('vox'); a.add_argument('volume'); a.add_argument('output'); a.add_argument('--step',type=int,required=True); a.add_argument('--roi')
    a=sub.add_parser('verify'); a.add_argument('output')
    x=p.parse_args()
    if x.command=='stats':
        from .statistics import run_legacy
        out=Path(x.output); out.mkdir(parents=True,exist_ok=False)
        print(json.dumps(run_legacy(x.data,out),indent=2))
    elif x.command=='ct-compare':
        from .statistics import compare_ct_blocks
        out=Path(x.output)
        with out.open('x',encoding='utf8') as f: compare_ct_blocks(x.csv).to_csv(f,index=False)
    elif x.command=='jpeg':
        from .workflows import run_jpeg
        run_jpeg(x.image,x.calibration,x.output,photo_key=x.photo_key,lots=[(x.lot,x.day)],nrows=x.rows,crop=x.crop,width_method=x.width_method)
    elif x.command=='vox':
        from .workflows import run_vox
        run_vox(x.volume,x.output,step=x.step,roi_path=x.roi)
    else:
        from .verification import run
        print(json.dumps(run(x.output),indent=2))
if __name__=='__main__': main()

