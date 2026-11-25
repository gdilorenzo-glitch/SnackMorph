"""Descriptive post-hoc review of frozen JPEG results; no estimator fitting."""
import argparse,zipfile
from pathlib import Path
import pandas as pd

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(Path(__file__).resolve().parent/'audit/final_validation.zip') as z:
        d=pd.read_csv(z.open('results/test_jpeg/metrics.csv'));w=pd.read_csv(z.open('results/test_jpeg/widths.csv'))
    d['relative_ED_error_pct']=100*(d.ED/d.ED_ref-1);d['absolute_Pk_error']=(d.Pk-d.Pk_ref).abs();d['absolute_Le_error']=(d.Le-d.Le_ref).abs()
    d.groupby('group').agg(n=('label','size'),matched=('matched','sum'),ED_median_pct=('relative_ED_error_pct','median'),Pk_MAE=('absolute_Pk_error','mean'),Le_MAE=('absolute_Le_error','mean')).to_csv(a.out/'jpeg_by_group.csv')
    pd.DataFrame([{'Dice_threshold':t,'objects':int((d.matched&(d.dice>=t)).sum()),'reference_objects':len(d)} for t in (0,.75,.90,.95)]).to_csv(a.out/'jpeg_match_thresholds.csv',index=False)
    d.loc[~d.matched,['image_id','group','variant','label','family']].to_csv(a.out/'jpeg_unmatched.csv',index=False)
    d[['relative_ED_error_pct','absolute_Pk_error','absolute_Le_error','R2']].describe(percentiles=[.05,.5,.95]).to_csv(a.out/'jpeg_error_summary.csv')
    w['signed_width_error_mm']=w.width_mm-w.width_ref_mm;w.groupby('group').signed_width_error_mm.agg(['size','mean','median','min','max']).to_csv(a.out/'jpeg_width_group.csv')
if __name__=='__main__':main()
