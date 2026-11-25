"""Independent analytical geometry and sRGB reference; no SnackMorph imports."""
import argparse,csv
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
F=np.array(sorted(set([round(x,3) for x in np.arange(.05,.951,.05)]+[.125,.375,.625,.875])))
def lab(rgb):
 c=np.array(rgb)/255.;c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);t=(np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]])@c)/[.95047,1,1.08883];d=6/29;f=np.where(t>d**3,np.cbrt(t),t/(3*d*d)+4/29);return (116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2]))
def save(path,rows):
 with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def geom(f,L,b,theta,cx,cy):
 s=(np.asarray(f)-.5)*L;k=b/L;x=s if b==0 else np.sin(k*s)/k;y=np.zeros_like(s) if b==0 else (1-np.cos(k*s))/k;c,t=np.cos(theta),np.sin(theta);a=theta+k*s;return np.stack([cx+c*x-t*y,cy+t*x+c*y],-1),np.stack([-np.sin(a),np.cos(a)],-1)
def diam(f,di,A,w,m,family):
 f=np.asarray(f);return di+A*np.exp(-(abs(f-(.42 if family=='asymmetric' else .5))/w)**m)*(0.85+.30*f if family=='asymmetric' else 1)
def main(out):
 out=Path(out);(out/'images').mkdir(parents=True,exist_ok=True);(out/'labels').mkdir(exist_ok=True);images=[];objects=[];profiles=[]
 variants=[('clean',1,98,0,0,0),('jpeg55',1,55,0,0,0),('illumination',1,85,2,12,.6),('resize75',.75,90,0,0,.4),('resize50',.5,75,1,0,.5)]
 for g in range(20):
  group=f'J{g+1:02}';split='development' if g<8 else 'test';rng=np.random.default_rng(702000+g);specs=[];family=['constant','flat_top','curved_flat_top','asymmetric'][g%4]
  for r in range(6):
   for c in range(3):
    theta=rng.uniform(-.055,.055);bend=rng.uniform(-.22,.22) if g%4 in (2,3) else 0.
    for a in range(2):
     di=rng.uniform(22,29);A=0 if g%4==0 else rng.uniform(9,23);w=rng.uniform(.24,.39);m=rng.uniform(2,5);L=rng.uniform(275,345);rgb=tuple(map(int,[rng.integers(185,241),rng.integers(103,151),rng.integers(25,65)]));specs.append((r,c,a,di,A,w,m,L,bend,theta,255+c*510+rng.uniform(-6,6),140+r*220+(a-.5)*64,rgb))
  for vi,(name,scale,quality,noise,grad,blur) in enumerate(variants):
   iid=f'{group}_{name}';W,H=round(1536*scale),round(1440*scale);px=.025/scale;im=Image.new('RGB',(W,H),(238,238,238));labels=Image.new('I',(W,H),0);draw=ImageDraw.Draw(im);ld=ImageDraw.Draw(labels);f=np.linspace(0,1,101)
   for r,c,a,di,A,w,m,L,bend,theta,cx,cy,rgb in specs:
    oid=r*6+c*2+a+1;p,n=geom(f,L,bend,theta,cx,cy);d=diam(f,di,A,w,m,family);left=p+n*d[:,None]/2;right=p-n*d[:,None]/2;poly=[tuple(q) for q in np.vstack([left,right[::-1]])*scale];ld.polygon(poly,fill=oid);draw.polygon(poly,fill=rgb)
    gradient=g%2==1
    if gradient:
     for j in range(len(f)-1):
      b=tuple(int(x*(.83+.17*abs(2*f[j]-1))) for x in rgb);draw.polygon([tuple(q*scale) for q in [left[j],left[j+1],right[j+1],right[j]]],fill=b)
    l,aa,bb=lab(rgb) if not gradient else ('','','');D=diam(np.linspace(0,1,10001),di,A,w,m,family);flat=family in ('flat_top','curved_flat_top')
    objects.append(dict(image_id=iid,group=group,split=split,label=oid,row=r,col=c,object_in_cell=a+1,family=family,pixel_size_mm=px,length_mm=L*.025,d_initial_mm=di*.025,ED_ref=np.mean(diam([.125,.375,.625,.875],di,A,w,m,family))/di,Pk_true=D.max()/di,Pk_model_ref=(di+A)/di if flat else '',Le_model_ref=np.exp(-(abs(np.linspace(0,1,201)-.5)/w)**m).mean() if flat else '',centre_diameter_mm=diam([.5],di,A,w,m,family)[0]*.025,curvature_rad=bend,rotation_rad=theta,nominal_R=rgb[0],nominal_G=rgb[1],nominal_B=rgb[2],uniform_colour=not gradient,L_ref=l,a_ref=aa,b_ref=bb))
    pp,nn=geom(F,L,bend,theta,cx,cy);dd=diam(F,di,A,w,m,family)
    for q,point,normal,width in zip(F,pp,nn,dd):
     col=rgb if not gradient else tuple(int(x*(.83+.17*abs(2*q-1))) for x in rgb);ll,aaa,bbb=lab(col);profiles.append(dict(image_id=iid,label=oid,fraction=q,diameter_mm=width*.025,centre_x_px=point[0]*scale,centre_y_px=point[1]*scale,normal_x=normal[0],normal_y=normal[1],nominal_L=ll,nominal_a=aaa,nominal_b=bbb))
   if blur:im=im.filter(ImageFilter.GaussianBlur(blur))
   if noise or grad:
    ar=np.asarray(im,dtype=np.float32).copy();ar+=np.linspace(-grad,grad,W,dtype=np.float32)[None,:,None];ar+=np.random.default_rng(987000+g*10+vi).normal(0,noise,ar.shape).astype(np.float32);im=Image.fromarray(np.clip(ar,0,255).astype(np.uint8))
   im.save(out/'images'/f'{iid}.jpg',quality=quality,subsampling=0);Image.fromarray(np.asarray(labels,dtype=np.uint16)).save(out/'labels'/f'{iid}.png');images.append(dict(image_id=iid,group=group,split=split,variant=name,scale=scale,width=W,height=H,pixel_size_mm=px,jpeg_quality=quality,noise_sd_rgb=noise,illumination_gradient_rgb=grad,blur_sigma_px=blur,rows=6,columns=3,objects=36,seed=702000+g))
  print(group,flush=True)
 for name,rows in [('manifest',images),('objects_truth',objects),('profiles_truth',profiles)]:save(out/f'{name}.csv',rows)
 (out/'README.md').write_text('''# Independent synthetic JPEG benchmark\n100 images, 20 distinct geometric scenes, five acquisition variants each; eight development and twelve test scenes. Each image has 36 labelled instances. The reference is rasterised from analytic shapes; geometry is defined in mm, independent of SnackMorph and its calibration. ED uses four positions (.125,.375,.625,.875); Le and model Pk are defined only for positive symmetric flat-top profiles. The 23 positions match the measurement definition. Nominal colour is calculated with standard sRGB/D65 equations independently, not a camera calibration. Gradient colour targets are pointwise nominal values, not exact window medians. JPEG and illumination intentionally change observed colour. Match A/B by spatial overlap, not order. Use independent mm/pixel, not the reference diameter for calibration. Use raw Lab for ideal colour validation; assess correction separately. Test is held out by geometry, not cryptographically blind: freeze code/criteria before evaluating it. Variants are correlated; do not count them as independent specimens.\n''')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);main(p.parse_args().out)
