"""JPEG algorithms, preserved from the author notebook. See audit for limitations."""
import os, glob, time
import numpy as np
import pandas as pd
# --- Original notebook cell 6 (zero-based) ---
import cv2
from scipy import ndimage as ndi
from skimage.segmentation import watershed
from skimage.morphology import skeletonize
from sklearn.cluster import KMeans
from scipy.spatial import cKDTree

def get_mask(im, crop=None):
    """Maschera arancione in HSV; i buchi < 400 px (pori) sono riempiti, lo sfondo tra due campioni no.
    crop=(y0,y1,x0,x1) azzera tutto cio' che e' fuori dalla zona della griglia."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[...,1]>95)&(hsv[...,0]>5)&(hsv[...,0]<35)&(hsv[...,2]>100)).astype(np.uint8)
    if crop is not None:
        y0,y1,x0,x1 = crop; z = np.zeros_like(m); z[y0:y1,x0:x1] = m[y0:y1,x0:x1]; m = z
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN,  np.ones((3,3),np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    filled = ndi.binary_fill_holes(m>0); holes = filled & ~(m>0)
    lh,kh = ndi.label(holes); szh = ndi.sum(holes,lh,range(1,kh+1))
    small = np.isin(lh,[j+1 for j,s in enumerate(szh) if s<400])
    return (m>0)|small, hsv

def cell_regions(mask, nrows, ncols=3):
    """Griglia: k-means sulle x dei componenti (colonne); entro ogni colonna le righe sono gruppi di y separati da gap > 21 px
    (si uniscono i gap piu' piccoli se i gruppi sono troppi, si divide il piu' esteso se sono pochi)."""
    lab,n = ndi.label(mask); comps=[]
    for i in range(1,n+1):
        a=(lab==i).sum()
        if a<400: continue
        ys,xs=np.nonzero(lab==i)
        if max(ys.max()-ys.min(), xs.max()-xs.min())<90: continue          # scarta macchie piccole
        comps.append((i,xs.mean(),ys.mean(),a))
    cx=np.array([c[1] for c in comps]).reshape(-1,1)
    km=KMeans(ncols,n_init=10,random_state=0).fit(cx)
    order=np.argsort(km.cluster_centers_.ravel()); remap={int(o):j for j,o in enumerate(order)}
    colof={comps[j][0]:remap[int(km.labels_[j])] for j in range(len(comps))}
    cens={}
    for c in range(ncols):
        sel=[x for x in comps if colof[x[0]]==c]
        yy=np.concatenate([np.nonzero(lab==x[0])[0] for x in sel])
        prof=np.bincount(yy,minlength=mask.shape[0]); on=np.nonzero(prof>0)[0]
        runs=[]; s=on[0]; p=on[0]
        for y in on[1:]:
            if y-p>21: runs.append((s,p)); s=y
            p=y
        runs.append((s,p))
        groups=[yy[(yy>=a)&(yy<=b)] for a,b in runs]
        while len(groups)>nrows:
            gaps=[runs[i+1][0]-runs[i][1] for i in range(len(runs)-1)]; j=int(np.argmin(gaps))
            runs[j]=(runs[j][0],runs[j+1][1]); del runs[j+1]
            groups=[yy[(yy>=a)&(yy<=b)] for a,b in runs]
        while len(groups)<nrows:
            j=int(np.argmax([g.max()-g.min() for g in groups])); v=groups.pop(j)
            k=KMeans(2,n_init=5,random_state=0).fit(v.reshape(-1,1)); cc=k.cluster_centers_.ravel()
            groups.insert(j,v[k.labels_==int(np.argmax(cc))]); groups.insert(j,v[k.labels_==int(np.argmin(cc))])
        cens[c]=np.sort(np.array([g.mean() for g in groups]))
    cells={}
    for x in comps:
        c=colof[x[0]]; ys,xs=np.nonzero(lab==x[0])
        rr=np.argmin(abs(ys[:,None]-cens[c][None,:]),axis=1)
        for r in np.unique(rr):
            key=(int(r),c); cells.setdefault(key,np.zeros(mask.shape,bool)); cells[key][ys[rr==r],xs[rr==r]]=True
    return cells

def split_cell(reg, V, Vloc):
    """Separa i due campioni di una cella: (1) solco scuro, (2) erosione progressiva, (3) taglio perpendicolare all'asse principale; poi watershed."""
    dt=ndi.distance_transform_edt(reg); tot=reg.sum()
    seam=(V<Vloc-6)&reg
    cut=ndi.binary_opening(reg&~ndi.binary_dilation(seam,iterations=1),iterations=2)
    l,k=ndi.label(cut); sz=np.array(ndi.sum(cut,l,range(1,k+1))) if k else np.array([])
    big=[j+1 for j,s in enumerate(sz) if s>0.12*tot]; how='solco'
    if len(big)>=2: big=sorted(big,key=lambda j:-sz[j-1])[:2]
    else:
        big=[]; how='erosione'
        for thr in (0.12,0.04):
            for e in np.arange(1.0,14,0.5):
                er=dt>e; l,k=ndi.label(er)
                if k==0: break
                sz=np.array(ndi.sum(er,l,range(1,k+1))); bb=[j+1 for j,s in enumerate(sz) if s>thr*tot]
                if len(bb)==2: big=bb; break
            if big: break
    if len(big)!=2:
        ys,xs=np.nonzero(reg); P=np.c_[xs,ys].astype(float); mu=P.mean(0)
        u,s_,vt=np.linalg.svd(P-mu,full_matrices=False); perp=(P-mu)@vt[1]
        c0,c1=np.percentile(perp,25),np.percentile(perp,75)
        for _ in range(30):
            a=abs(perp-c0)<abs(perp-c1); c0,c1=perp[a].mean(),perp[~a].mean()
        a=abs(perp-c0)<abs(perp-c1); out=[]
        for sel in (a,~a):
            z=np.zeros(reg.shape,bool); z[ys[sel],xs[sel]]=True; out.append(z)
        return out,'perp'
    mk=np.zeros(reg.shape,int)
    for q,j in enumerate(big): mk[l==j]=q+1
    vv=(V[reg]-V[reg].mean())/(V[reg].std()+1e-6)
    elev=np.zeros(reg.shape,np.float32); elev[reg]=-(dt[reg]/dt.max())-0.5*vv
    ws=watershed(elev,mk,mask=reg)
    return [ws==1,ws==2],how

def refine_with_chroma(im, cells, TH=16, grow=18):
    """Raffinamento: la maschera HSV e' estesa ai pixel con crominanza CIELAB (8 bit, piano a*b*) > TH entro 'grow' px;
    ogni pixel nuovo va al campione piu' vicino. Restituisce, per cella, il riquadro e le maschere A e B ritagliate."""
    lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
    chroma=np.hypot(lab[...,1]-128,lab[...,2]-128); fg=ndi.binary_opening(chroma>TH,np.ones((3,3)))
    out={}
    for key,(a,b) in cells.items():
        old=a|b; ys,xs=np.nonzero(old); y0,y1,x0,x1=max(ys.min()-30,0),ys.max()+31,max(xs.min()-30,0),xs.max()+31
        o=old[y0:y1,x0:x1]; A=a[y0:y1,x0:x1]; B=b[y0:y1,x0:x1]
        near=ndi.binary_dilation(o,iterations=grow); reg=(fg[y0:y1,x0:x1]&near)|o
        l,k=ndi.label(reg); keep=np.unique(l[o]); keep=keep[keep>0]; reg=ndi.binary_fill_holes(np.isin(l,keep))
        dist,(iy,ix)=ndi.distance_transform_edt(~o,return_indices=True)
        nearest=np.where(A,1,np.where(B,2,0))[iy,ix]
        out[key]=dict(box=(y0,y1,x0,x1),A=reg&((nearest==1)|A)&~B,B=reg&((nearest==2)|B)&~A)
    return out

def segment_photo(path, nrows, crop=None):
    """Foto -> (immagine BGR, {(riga,colonna): dict(box, A, B)}) con le maschere raffinate dei due campioni."""
    im=cv2.imread(path); assert im is not None, f'foto non leggibile: {path}'
    mask,hsv=get_mask(im,crop)
    V=cv2.GaussianBlur(hsv[...,2].astype(np.float32),(0,0),1.5); Vloc=cv2.GaussianBlur(hsv[...,2].astype(np.float32),(0,0),9)
    cells=cell_regions(mask,nrows); split={}
    for k,reg in sorted(cells.items()): split[k],_=split_cell(reg,V,Vloc)
    return im, refine_with_chroma(im,split)

def overlay_photo(im, samples, scale=0.4):
    """Controllo visivo: campione A in rosso, B in blu, indici di cella (riga,colonna)."""
    ov=im.copy(); cols=[(0,0,255),(255,0,0)]
    for (r,c),d in samples.items():
        y0,y1,x0,x1=d['box']
        for k,m in enumerate((d['A'],d['B'])):
            sub=ov[y0:y1,x0:x1]; sub[m]=(0.45*sub[m]+0.55*np.array(cols[k])).astype(np.uint8)
    ov=cv2.resize(ov,None,fx=scale,fy=scale)
    for (r,c),d in samples.items():
        y0,y1,x0,x1=d['box']; ys,xs=np.nonzero(d['A']|d['B'])
        cv2.putText(ov,f'{r},{c}',(int((xs.min()+x0)*scale)-34,int((ys.mean()+y0)*scale)+4),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,0,0),1,cv2.LINE_AA)
    return cv2.cvtColor(ov,cv2.COLOR_BGR2RGB)

# --- Original notebook cell 8 (zero-based) ---
from scipy.ndimage import map_coordinates

def clean(mk):
    """Apertura 3x3, componente piu' grande, riempimento dei buchi."""
    mk=ndi.binary_opening(mk,np.ones((3,3))); l,k=ndi.label(mk)
    if k>1:
        sz=ndi.sum(mk,l,range(1,k+1)); mk=(l==(1+int(np.argmax(sz))))
    return ndi.binary_fill_holes(mk)

def axis_pca(mk, deg=3, binw=3.0):
    """Asse curvo: PCA del contorno, centroidi (mediana trasversale) in bin di 3 px lungo l'asse principale, polinomio cubico pesato."""
    ys,xs=np.nonzero(mk); P=np.c_[xs,ys].astype(float); mu=P.mean(0)
    u_,s_,vt=np.linalg.svd(P-mu,full_matrices=False); u,w=vt[0],vt[1]
    s=(P-mu)@u; v=(P-mu)@w
    edges=np.arange(s.min(),s.max()+binw,binw); idx=np.digitize(s,edges); cs=[];cv_=[];cw=[]
    for b in np.unique(idx):
        m=idx==b
        if m.sum()>=5: cs.append(s[m].mean()); cv_.append(np.median(v[m])); cw.append(m.sum())
    poly=np.poly1d(np.polyfit(cs,cv_,deg,w=np.sqrt(cw)))
    sg=np.arange(s.min(),s.max(),1.0); vg=poly(sg)
    return mu[None,:]+sg[:,None]*u[None,:]+vg[:,None]*w[None,:]

def chord(mk,x,y,nx,ny,tmax=60):
    """Lunghezza della corda lungo la normale (nx,ny) nel punto (x,y): segmento di maschera contenente (o piu' vicino a) l'asse."""
    t=np.arange(-tmax,tmax+0.01,0.5)
    v=map_coordinates(mk.astype(float),[y+t*ny,x+t*nx],order=0,mode='constant',cval=0)>0.5
    if not v.any(): return 0.0,0.0,0.0
    d=np.diff(np.r_[0,v.astype(int),0]); st=np.nonzero(d==1)[0]; en=np.nonzero(d==-1)[0]-1
    i0=len(t)//2; best=None
    for a_,b_ in zip(st,en):
        dist=0 if a_<=i0<=b_ else min(abs(a_-i0),abs(b_-i0))*0.5
        if dist>15: continue
        if dist==0: best=(0,a_,b_); break
        if best is None or (b_-a_)>(best[2]-best[1]): best=(dist,a_,b_)
    if best is None: return 0.0,0.0,0.0
    dist,a_,b_=best
    return float(t[b_]-t[a_]+1.0),float(max(t[b_],0)),float(max(-t[a_],0))


def chord_subpixel(mk, x, y, nx, ny):
    """Length of the 0.5 isocontour of a bilinearly interpolated binary mask.

    Quarter-pixel sampling and linear interpolation of threshold crossings;
    not a correction for rasterisation or a continuous optical ground truth.
    """
    norm = np.hypot(nx, ny)
    if not np.isfinite(norm) or norm == 0:
        raise ValueError('invalid normal')
    nx, ny = nx/norm, ny/norm
    # Restrict the line to the padded image rectangle, including zero exterior.
    mask = np.pad(np.asarray(mk, dtype=np.float32), 1)
    x, y = x+1, y+1
    low, high = -np.inf, np.inf
    for q, d, limit in ((x,nx,mask.shape[1]-1),(y,ny,mask.shape[0]-1)):
        if abs(d) < 1e-12:
            if not 0 <= q <= limit: return 0.,0.,0.
        else:
            a,b=sorted((-q/d,(limit-q)/d)); low=max(low,a); high=min(high,b)
    if high <= low: return 0.,0.,0.
    t=np.linspace(low,high,max(2,int(np.ceil((high-low)/.25))+1))
    v=map_coordinates(mask,[y+t*ny,x+t*nx],order=1,mode='constant',cval=0)
    inside=v>=.5
    edges=np.diff(np.r_[False,inside,False].astype(np.int8))
    starts=np.flatnonzero(edges==1); ends=np.flatnonzero(edges==-1)-1
    if not len(starts): return 0.,0.,0.
    def distance(a,b): return max(t[a],-t[b],0.)
    a,b=min(zip(starts,ends),key=lambda ab:(distance(*ab),-(ab[1]-ab[0])))
    if distance(a,b)>15: return 0.,0.,0.
    def cross(i,j):
        return t[i]+(.5-v[i])*(t[j]-t[i])/(v[j]-v[i])
    left=cross(a-1,a) if a>0 else t[a]
    right=cross(b,b+1) if b+1<len(t) else t[b]
    return float(right-left),float(max(right,0)),float(max(-left,0))

FRACS = sorted(set([round(x,3) for x in np.arange(0.05,0.951,0.05)]+[0.125,0.375,0.625,0.875]))   # 23 posizioni relative

def width_normals(mk, fracs=FRACS, win=0.02, *, method="legacy"):
    """Larghezza (px) del campione in ogni posizione relativa f della lunghezza L dell'asse: mediana di corde perpendicolari
    all'asse su una finestra ±win*L (passo 2 px). Restituisce ({f: larghezza_px}, L_px)."""
    if method not in ("legacy", "subpixel"): raise ValueError(method)
    chord_fn = chord if method == "legacy" else chord_subpixel
    ys_,xs_=np.nonzero(mk); oy,ox=max(ys_.min()-15,0),max(xs_.min()-15,0)
    mk=clean(mk[oy:ys_.max()+16,ox:xs_.max()+16])
    ax=axis_pca(mk); seg=np.r_[0,np.cumsum(np.hypot(*np.diff(ax,axis=0).T))]; L=seg[-1]; res={}
    for f in fracs:
        ws=[]
        for ds in np.arange(-win*L,win*L+0.1,2.0):
            s=min(max(f*L+ds,0),L); i=int(np.searchsorted(seg,s)); i=min(max(i,1),len(ax)-2)
            i0,i1=max(i-4,0),min(i+4,len(ax)-1); t=ax[i1]-ax[i0]; t=t/(np.hypot(*t)+1e-9); nx,ny=-t[1],t[0]
            x,y=ax[i]; w,a,b=chord_fn(mk,x,y,nx,ny); ws.append(w)
        res[f]=float(np.median(ws))
    return res,L

# --- Original notebook cell 10 (zero-based) ---
# ----------------------------------------------------------------------------------------------------------------------
# Manifest: foto -> lotti, giorni di conservazione dei pellet, nomi file, numero di righe.
#   0 d : 10 righe (5 MW + 5 MWF);  15 e 30 d : 6 righe (3 MW + 3 MWF).
#   Colonne = potenza 40, 60, 80 %.  Il campo 'crop' (y0,y1,x0,x1) isola la griglia quando la foto contiene altri oggetti.
#   I nomi file sono quelli dei JPEG originali (WhatsApp_Image_2026-10-07_at_...); adattarli se rinominati.
# ----------------------------------------------------------------------------------------------------------------------
PHOTOS = {
 'B02_0' : dict(file='WhatsApp_Image_2026-10-07_at_10_46_54.jpeg',    nrows=10, crop=(700,2300,600,1700), lots=[('B-02',0)]),
 'B03_0' : dict(file='WhatsApp_Image_2026-10-07_at_10_46_53__1_.jpeg', nrows=10, crop=None, lots=[('B-03',0)]),
 'B02_15': dict(file='WhatsApp_Image_2026-10-07_at_10_46_53.jpeg',    nrows=6,  crop=None, lots=[('B-02',15)]),
 'B03_15': dict(file='WhatsApp_Image_2026-10-07_at_10_46_52__1_.jpeg', nrows=6,  crop=None, lots=[('B-03',15)]),
 'B04_15': dict(file='WhatsApp_Image_2026-10-07_at_10_46_52.jpeg',    nrows=6,  crop=None, lots=[('B-04',15)]),
 'B02_30': dict(file='WhatsApp_Image_2026-10-07_at_10_46_50__1_.jpeg', nrows=6,  crop=None, lots=[('B-02',30)]),
 'B03_30': dict(file='WhatsApp_Image_2026-10-07_at_10_46_51.jpeg',    nrows=6,  crop=None, lots=[('B-03',30)]),
 'B04_30': dict(file='WhatsApp_Image_2026-10-07_at_10_46_50.jpeg',    nrows=6,  crop=None, lots=[('B-04',30)]),
}
POWERS = [40,60,80]
TAU_DAY0_B02_MWF = [.25,.375,.5,.75,1]      # il giorno 0 del lotto B-02 per MWF ha tempi diversi (nell'analisi statistica -> tau_scala .2 .4 .6 .8 1)
TAU_SCALA = {0.25:0.2,0.375:0.4,0.5:0.6,0.75:0.8,1.0:1.0}

def layout(photo_key, r, c, lot):
    """(riga, colonna) della foto -> (tecnologia, potenza, tau) secondo lo schema sperimentale."""
    t = 0 if photo_key.endswith('_0') else 1
    if t==0:
        tech='MW' if r<5 else 'MWF'
        tau = TAU_DAY0_B02_MWF[r%5] if (photo_key=='B02_0' and tech=='MWF') else [.2,.4,.6,.8,1][r%5]
    else:
        tech='MW' if r<3 else 'MWF'; tau=[.4,.6,.8][r%3]
    return tech, POWERS[c], round(tau,3)

def load_caliper(path):
    """campioni_espansione.csv -> per cella (lotto,t_gg,tecnologia,potenza,tau): diametro iniziale del pellet e diametro finale al calibro."""
    S=pd.read_csv(path)
    return S.groupby(['lotto','t_gg','tecnologia','potenza','tau']).agg(d_ini=('d_ini','first'),d_cal=('d_fin_cal','first')).reset_index()

def profile_table(samples, photo_key, lots, cal, *, width_method="legacy"):
    """Per ogni cella e lotto: larghezze in px -> mm con k = d_cal / media(larghezza a f=0.5 dei due campioni); righe per campione e posizione."""
    rows=[]
    for (r,c),d in sorted(samples.items()):
        ws=[width_normals(m, method=width_method) for m in (d['A'],d['B'])]
        for lot,t in lots:
            tech,pw,tau=layout(photo_key,r,c,lot)
            q=cal[(cal.lotto==lot)&(cal.t_gg==t)&(cal.tecnologia==tech)&(cal.potenza==pw)&(np.isclose(cal.tau,tau))]
            if q.empty: continue
            di,dfn=float(q.d_ini.iloc[0]),float(q.d_cal.iloc[0])
            if not np.isfinite(dfn): continue
            k=dfn/np.mean([w[0.5] for w,_ in ws])          # mm/px della cella
            for s,(w,L) in enumerate(ws,1):
                for f in FRACS: rows.append(dict(lotto=lot,t_gg=t,tecnologia=tech,potenza=pw,tau=tau,campione=s,d_ini=di,d_cal=dfn,L_mm=L*k,f=f,D=k*w[f]))
    return pd.DataFrame(rows)

# --- Original notebook cell 12 (zero-based) ---
from scipy.optimize import least_squares

def profile_model(f, Di, A, s, m):
    """D(x) = Di + A * exp(-(|x-0.5|/s)^m): profilo a plateau centrale (s = larghezza, m = ripidita' dei fianchi)."""
    return Di + A*np.exp(-(np.abs(f-0.5)/s)**m)

def fit_profile(f, D, Di):
    """Minimi quadrati (3 partenze, limiti A in [0,3Dmax], s in [0.05,1], m in [1,12]).
    P_k = (Di+A)/Di ; L_e = media di exp(-(|x-0.5|/s)^m) su [0,1] ; ED_model = 1 + (A/Di) L_e ; R2 del profilo."""
    best=None
    for s0,m0 in [(0.3,2),(0.2,4),(0.5,2)]:
        try: r=least_squares(lambda p:profile_model(f,Di,p[0],p[1],p[2])-D,[max(D.max()-Di,0.2),s0,m0],bounds=([0,0.05,1],[3*D.max(),1.0,12]))
        except Exception: continue
        if best is None or r.cost<best.cost: best=r
    A,s,m=best.x; fit=profile_model(f,Di,A,s,m); ss_res=((D-fit)**2).sum(); ss_tot=((D-D.mean())**2).sum()
    ff=np.linspace(0,1,201); Le=float(np.exp(-(np.abs(ff-0.5)/s)**m).mean())
    return dict(a=A,s=s,m=m,Pk=(Di+A)/Di,Le=Le,ED_model=1+A/Di*Le,R2=1-ss_res/ss_tot)

def fit_all_profiles(P):
    """P = tabella dei profili (profile_table). ED = media dei diametri a f = .125,.375,.625,.875 / d_ini (4 posizioni fuori dal centro)."""
    keys=['lotto','t_gg','tecnologia','potenza','tau','campione']; rec=[]
    for k,g in P.groupby(keys):
        g=g.sort_values('f'); Di=float(g.d_ini.iloc[0]); r=fit_profile(g.f.values,g.D.values,Di)
        d4=g[g.f.isin([0.125,0.375,0.625,0.875])].D.mean()
        rec.append(dict(zip(keys,k),d_ini=Di,ED=d4/Di,L_mm=g.L_mm.iloc[0],**r))
    F=pd.DataFrame(rec).rename(columns={'t_gg':'periodo'})
    F['tau_scala']=[TAU_SCALA.get(t,t) for t in F.tau]
    F['id']=F.lotto+'|'+F.periodo.astype(str)+'|'+F.tecnologia+'|'+F.potenza.astype(str)+'|'+F.tau.astype(str)+'|'+F.campione.astype(str)
    return F[['id','lotto','periodo','tecnologia','potenza','tau','tau_scala','campione','d_ini','a','s','m','Pk','Le','ED','ED_model','R2','L_mm']]

# --- Original notebook cell 13 (zero-based) ---
# ------------------------------------------------------------------ colore CIELAB
def photo_lab(im, samples):
    """Immagine in CIELAB (float: L 0-100, a/b con segno) e colore del fondo = mediana dei pixel neutri e chiari
    (crominanza < 10, L > 45) lontani > 60 px dai campioni, entro il riquadro della griglia (+150 px)."""
    lab=cv2.cvtColor(im.astype(np.float32)/255.0,cv2.COLOR_BGR2LAB); H,W=im.shape[:2]; allm=np.zeros((H,W),bool)
    for d in samples.values():
        y0,y1,x0,x1=d['box']; allm[y0:y1,x0:x1]|=d['A']|d['B']
    ys,xs=np.nonzero(allm); box=(max(ys.min()-150,0),ys.max()+150,max(xs.min()-150,0),xs.max()+150)
    near=ndi.binary_dilation(allm,iterations=60); reg=np.zeros((H,W),bool); reg[box[0]:box[1],box[2]:box[3]]=True
    chroma=np.hypot(lab[...,1],lab[...,2]); bg=reg&~near&(chroma<10)&(lab[...,0]>45)
    return lab, np.median(lab[bg],axis=0)

def colour_tables(photo_data, lots_of_photo):
    """photo_data[key] = (im, samples, lab, bg). Colore del campione = mediana di L,a,b sul corpo centrale (±30 % della lunghezza,
    eroso di 3 px); profili = mediana in finestre di ±2.5 % L lungo l'asse (>= 30 px). Correzione del fondo: L riportata al fondo
    mediano comune (Lref), a e b per sottrazione del fondo della propria foto."""
    Lref=float(np.median([v[3][0] for v in photo_data.values()])); rows=[]; prof=[]
    for key,(im,samples,lab,bg) in photo_data.items():
        for (r,c),d in sorted(samples.items()):
            y0,y1,x0,x1=d['box']; sub=lab[y0:y1,x0:x1]
            for lot,t in lots_of_photo[key]:
                tech,pw,tau=layout(key,r,c,lot)
                for k,m in enumerate((d['A'],d['B']),1):
                    ys,xs=np.nonzero(m); P=np.c_[xs,ys].astype(float); mu=P.mean(0)
                    u=np.linalg.svd(P-mu,full_matrices=False)[2][0]; s=(P-mu)@u; mid=np.median(s); half=0.3*(s.max()-s.min())
                    body=np.zeros_like(m); body[ys[np.abs(s-mid)<=half],xs[np.abs(s-mid)<=half]]=True; body&=ndi.binary_erosion(m,iterations=3)
                    Lm,am,bm=[float(np.median(sub[...,i][body])) for i in range(3)]
                    sid=f'{lot}|{t}|{tech}|{pw}|{tau}|{k}'
                    rows.append(dict(id=sid,lotto=lot,periodo=t,tecnologia=tech,potenza=pw,tau=tau,tau_scala=TAU_SCALA.get(tau,tau),campione=k,L=Lm,a=am,b=bm,
                                     Lc=Lm+(Lref-bg[0]),ac=am-bg[1],bc=bm-bg[2]))
                    mk=clean(m); ax=axis_pca(mk); seg=np.r_[0,np.cumsum(np.hypot(*np.diff(ax,axis=0).T))]; L=seg[-1]
                    inner=ndi.binary_erosion(mk,iterations=3); yy,xx=np.nonzero(inner); _,idx=cKDTree(ax).query(np.c_[xx,yy].astype(float)); arc=seg[idx]; vals=sub[yy,xx]
                    for f in FRACS:
                        sel=np.abs(arc-f*L)<=0.025*L
                        if sel.sum()<30: continue
                        l_,a_,b_=[float(np.median(vals[sel,i])) for i in range(3)]
                        prof.append(dict(id=sid,posizione=round(f*100,1),Lc=l_+(Lref-bg[0]),ac=a_-bg[1],bc=b_-bg[2],npix=int(sel.sum())))
    return pd.DataFrame(rows), pd.DataFrame(prof), Lref

def fit_colour_profiles(Pc):
    """Per ogni profilo e canale (L*, a*, b*): valore di riferimento = media delle posizioni <= 10 % e >= 90 %;
    modello 1 + g*exp(-(|x-0.5|/s)^m) sui valori divisi per il riferimento (stesso fit del diametro). Restituisce ref, g, s, m, Le, R2."""
    out=[]
    for i,g in Pc.groupby('id'):
        g=g.sort_values('posizione'); x=g.posizione.values/100; row={'id':i}
        for ch,col in (('L','Lc'),('a','ac'),('b','bc')):
            y=g[col].values; ref=float(y[(g.posizione.values<=10)|(g.posizione.values>=90)].mean()); z=y/ref; best=None
            for s0,m0 in [(.3,2),(.2,4),(.5,2)]:
                r=least_squares(lambda p:1+p[0]*np.exp(-(np.abs(x-.5)/p[1])**p[2])-z,[0.05,s0,m0],bounds=([-3,0.05,1],[3,1,12]))
                if best is None or r.cost<best.cost: best=r
            p=best.x; fit=1+p[0]*np.exp(-(np.abs(x-.5)/p[1])**p[2]); Le=float(np.exp(-(np.abs(np.linspace(0,1,201)-.5)/p[1])**p[2]).mean())
            row.update({f'ref_{ch}':ref,f'g_{ch}':p[0],f's_{ch}':p[1],f'm_{ch}':p[2],f'Le_{ch}':Le,f'R2_{ch}':1-((z-fit)**2).sum()/((z-z.mean())**2).sum()})
        out.append(row)
    return pd.DataFrame(out)

def synthetic_photo(nrows=6, W=1932, H=2576, seed=0):
    """Foto sintetica: fondo bianco, 3 colonne x nrows righe; in ogni cella due 'estrusi' (A sopra, B sotto) lunghi 330 px con diametro
    D(x) = Di + A exp(-(|x-.5|/s)^m) (px), orientati in orizzontale, separati da un sottile solco scuro."""
    rng=np.random.default_rng(seed); im=np.full((H,W,3),245,np.uint8); truth={}
    xs=np.array([330,930,1530]); ys=np.linspace(520,2150,nrows)
    for r,y0 in enumerate(ys):
        for c,x0 in enumerate(xs):
            Di=26; A=rng.uniform(8,18); s=rng.uniform(.25,.4); m=rng.uniform(2,5)
            for k,(dy) in enumerate((-30,30)):
                L=330; xx=np.arange(L); fr=xx/L; D=profile_model(fr,Di,A,s,m)
                for x,d in zip(xx,D):
                    yc=y0+dy; cv2.line(im,(int(x0+x),int(yc-d/2)),(int(x0+x),int(yc+d/2)),(30,120,235),1)   # BGR arancione
            truth[(r,c)]=(Di,A,s,m)
    return cv2.GaussianBlur(im,(0,0),1.0), truth

def explicit_amplitude(fits):
    """Retain original a (mm) as A_mm; expose a=A_mm/Di unambiguously."""
    result = fits.copy()
    result['A_mm'] = result['a']
    result['a'] = result['A_mm'] / result['d_ini']
    return result

def colour_descriptors(table):
    """Additional descriptors of corrected Lab coordinates; no ΔE without reference."""
    result = table.copy()
    result['Cstar'] = np.hypot(result.ac, result.bc)
    result['h_deg'] = np.mod(np.degrees(np.arctan2(result.bc, result.ac)), 360)
    result.loc[result.Cstar == 0, 'h_deg'] = np.nan
    return result

def delta_e76(Lab, reference):
    """Explicit CIE76 reference (last dimension must be L*,a*,b*)."""
    x, y = np.asarray(Lab, float), np.asarray(reference, float)
    if x.ndim == 0 or y.ndim == 0 or x.shape[-1] != 3 or y.shape[-1] != 3:
        raise ValueError('Lab and reference must have last dimension 3')
    return np.linalg.norm(x-y, axis=-1)

