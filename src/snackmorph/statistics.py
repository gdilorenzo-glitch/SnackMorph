"""Legacy statistical workflow, unchanged equations and models; compare CT block separately."""
from pathlib import Path
import os, json, itertools, math, re, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_legacy(data_dir, output_dir):
    DATA_DIR = str(Path(data_dir).resolve())
    OUT_DIR = str(Path(output_dir).resolve())
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    RUN_C = True
    # --- Original notebook cell 44 (zero-based) ---
    CSV_DIR = DATA_DIR                      # oppure OUT_DIR, dopo aver eseguito le parti A e B
    THR = 2.5                               # soglia dello z modificato (MAD) per gli outlier
    REF_POWER, REF_TAU = 80, 0.8            # campione di riferimento per correlazioni, PCA, bilancio di massa
    if RUN_C:
        M  = pd.read_csv(f'{CSV_DIR}/modello_campioni.csv')
        Cc = pd.read_csv(f'{CSV_DIR}/colore_campioni.csv')
        B0 = pd.read_csv(f'{CSV_DIR}/bending_provini.csv')
        R  = pd.read_csv(f'{CSV_DIR}/tomo_riepilogo.csv'); R = R[R.trattamento.isin(['MW','MWF'])].copy()   # il non espanso e' un controllo: fuori dall'analisi
        M['tn']=M.tau_scala.round(1); Cc['tn']=Cc.tau_scala.round(1)           # tau nominale comune (.2 .4 .6 .8 1)
        print('campioni (profili):',len(M),'| colore:',len(Cc),'| provini a flessione:',len(B0),'| scansioni CT (MW/MWF):',len(R))

    # --- Original notebook cell 46 (zero-based) ---
    def mz(x):
        x=np.asarray(x,float); med=np.median(x); mad=np.median(np.abs(x-med)); return np.zeros(len(x)) if mad==0 else 0.6745*(x-med)/mad
    def flag(df,keys,col,thr=THR):
        return df.groupby(keys)[col].transform(lambda s: pd.Series(np.abs(mz(s.values))>thr,index=s.index)).astype(bool)

    if RUN_C:
        kc=['tecnologia','potenza','periodo','tn']
        M['out_ED']=flag(M,kc,'ED')
        M['poor_fit']=M.R2<0.5
        for q in ('Pk','Le'):
            ok=M[~M.poor_fit]; fl=flag(ok,kc,q); M['out_'+q]=M.poor_fit.copy(); M.loc[ok.index,'out_'+q]=fl
        for c,n in (('Lc','L'),('ac','a'),('bc','b')): Cc['out_'+n]=flag(Cc,kc,c)
        B=B0[B0.usato==True].rename(columns={'sforzo_max_MPa':'sigma','modulo_young_MPa':'E','deformazione_carico_max_pct':'eps','trattamento':'tec','tempo_gg':'g'}).copy()
        for c in ('sigma','E','eps'): B['out_'+c]=flag(B,['tec','g'],c)
        Mc=M[~M.out_ED].copy(); Mpk=M[~M.out_Pk].copy(); Mle=M[~M.out_Le].copy(); Mc['VEI']=Mc.ED**2*(Mc.L_mm/40.0)       # VEI: indice volumetrico, L0 = 40 mm
        OUT=pd.DataFrame([('ED',M.out_ED.sum(),len(M)),('Pk (R2<0.5 + MAD)',M.out_Pk.sum(),len(M)),('Le (R2<0.5 + MAD)',M.out_Le.sum(),len(M)),
            ('L*',Cc.out_L.sum(),len(Cc)),('a*',Cc.out_a.sum(),len(Cc)),('b*',Cc.out_b.sum(),len(Cc)),
            ('sigma_max',B.out_sigma.sum(),len(B)),('E',B.out_E.sum(),len(B)),('eps',B.out_eps.sum(),len(B))],columns=['grandezza','esclusi','su'])
        OUT['%']=(OUT.esclusi/OUT.su*100).round(1); print(OUT.to_string(index=False)); print('fit con R2 < 0.5:',int(M.poor_fit.sum()))
        OUT.to_csv(f'{OUT_DIR}/outlier_esclusi.csv',index=False)

    # --- Original notebook cell 48 (zero-based) ---
    from scipy.optimize import curve_fit
    def ed_kin(t,E,k): return 1+(E-1)*(1-np.exp(-k*t))
    def r2(y,yh): return 1-((y-yh)**2).sum()/((y-y.mean())**2).sum()
    if RUN_C:
        rows=[]
        for (tec,pot),g in Mc.groupby(['tecnologia','potenza']):
            g0=g[g.periodo==0]; p,cv=curve_fit(ed_kin,g0.tau_scala.values if False else g0.tau.values,g0.ED.values,p0=[1.8,3],bounds=([1,0.05],[4,60]),maxfev=20000); se=np.sqrt(np.diag(cv))
            rows.append(dict(tecnologia=tec,potenza=pot,periodo=0,ED_inf=p[0],ED_inf_se=se[0],k=p[1],k_se=se[1],R2=r2(g0.ED.values,ed_kin(g0.tau.values,*p)),n=len(g0)))
            for per in (15,30):
                gs=g[g.periodo==per]; fk=lambda t,E:ed_kin(t,E,p[1]); pe,cve=curve_fit(fk,gs.tau.values,gs.ED.values,p0=[1.7],bounds=([1],[4]))
                rows.append(dict(tecnologia=tec,potenza=pot,periodo=per,ED_inf=pe[0],ED_inf_se=np.sqrt(cve[0,0]),k=p[1],k_se=np.nan,R2=r2(gs.ED.values,fk(gs.tau.values,*pe)),n=len(gs)))
        KIN=pd.DataFrame(rows); KIN.round(3).to_csv(f'{OUT_DIR}/cinetica_ED.csv',index=False); print(KIN.round(3).to_string(index=False))

    # --- Original notebook cell 50 (zero-based) ---
    import statsmodels.formula.api as smf
    from patsy import dmatrices, dmatrix
    from scipy.stats import studentized_range

    def block_fit(d,val,cell='cell',lot='lotto'):
        """Modello y ~ C(cell) + C(lotto); restituisce il modello e, per ogni cella, il vettore di riga della media LS (media sui lotti)."""
        d=d.copy(); d['y']=d[val]; _,X=dmatrices(f'y ~ C({cell}) + C({lot})',d,return_type='dataframe'); di=X.design_info
        m=smf.ols(f'y ~ C({cell}) + C({lot})',data=d).fit(); lots=sorted(d[lot].unique()); rows={}
        for c in sorted(d[cell].unique()):
            rows[c]=np.asarray(dmatrix(di,pd.DataFrame({cell:c,lot:lots,'y':0.0}),return_type='dataframe')).mean(axis=0)
        return m,rows
    def lsm_se(m,rows):
        b=m.params.values; Cv=m.cov_params().values; return {c:(float(r@b),float(np.sqrt(max(r@Cv@r,0)))) for c,r in rows.items()}
    def adjusted(d,val,cell='cell',lot='lotto'): return lsm_se(*block_fit(d,val,cell,lot))
    def tukey_letters(m,rows,fam,alpha=0.05):
        b=m.params.values; Cv=m.cov_params().values; ls={c:float(rows[c]@b) for c in fam}; k=len(fam); qc=studentized_range.ppf(1-alpha,k,m.df_resid); sig=set()
        for i,a in enumerate(fam):
            for b_ in fam[i+1:]:
                v=rows[a]-rows[b_]; se=np.sqrt(max(v@Cv@v,1e-12))
                if abs(ls[a]-ls[b_])/se*np.sqrt(2)>qc: sig.add(frozenset((a,b_)))
        order=sorted(fam,key=lambda c:-ls[c]); cols=[set(order)]
        for pair in sig:                                    # algoritmo di assorbimento: gruppi massimali non significativi
            a,b_=tuple(pair); new=[]
            for c in cols:
                if a in c and b_ in c: new+=[c-{a},c-{b_}]
                else: new.append(c)
            cols=new
        cols=[c for c in cols if c]; cols=[c for i,c in enumerate(cols) if not any(c<e or (c==e and j<i) for j,e in enumerate(cols) if j!=i)]
        cols.sort(key=lambda c:min(order.index(n) for n in c))
        return {n:''.join(chr(97+i) for i,c in enumerate(cols) if n in c) for n in fam}

    # --- Original notebook cell 51 (zero-based) ---
    if RUN_C:
        rows=[]; LET={}
        # ---------- ED (Fig. 6): un modello per tecnologia con potenza x conservazione x tau; lettere sulla famiglia potenza x conservazione a tau = 0.8
        for tec in ('MW','MWF'):
            d=Mc[Mc.tecnologia==tec].groupby(['potenza','periodo','tn','lotto']).ED.mean().reset_index(); d['cell']=d.potenza.astype(str)+'|'+d.periodo.astype(str)+'|'+d.tn.astype(str)
            m,rw=block_fit(d,'ED')
            for c,(mu,se) in lsm_se(m,rw).items(): p,pe,t=c.split('|'); rows.append(('ED',tec,int(p),int(pe),float(t),mu,se))
            fam=[f'{p}|{per}|0.8' for p in (40,60,80) for per in (0,15,30)]; LET[f'ED_{tec}']={k.rsplit('|',1)[0]:v for k,v in tukey_letters(m,rw,fam).items()}
        # ---------- Pk e Le (Fig. 7), colore (Fig. 8): un modello per conservazione; famiglia tecnologia x potenza a tau = 0.8
        srcs=[('Pk',Mpk,'Pk'),('Le',Mle,'Le')]+[(n,Cc[~Cc[o]],c) for c,o,n in (('Lc','out_L','L*'),('ac','out_a','a*'),('bc','out_b','b*'))]
        for nm,src,col in srcs:
            for per in (0,15,30):
                d=src[src.periodo==per].groupby(['tecnologia','potenza','tn','lotto'])[col].mean().reset_index(); d['cell']=d.tecnologia+'|'+d.potenza.astype(str)+'|'+d.tn.astype(str)
                m,rw=block_fit(d,col)
                for c,(mu,se) in lsm_se(m,rw).items(): te,p,t=c.split('|'); rows.append((nm,te,int(p),per,float(t),mu,se))
                fam=[f'{t}|{p}|0.8' for t in ('MW','MWF') for p in (40,60,80)]; LET[f'{nm}_{per}']={k.rsplit('|',1)[0]:v for k,v in tukey_letters(m,rw,fam).items()}
        # ---------- flessione (Fig. 11): un modello per grandezza, condizioni = tecnologia x conservazione
        for c,nm in (('sigma','sigma_max_MPa'),('E','E_MPa'),('eps','eps_pct')):
            d=B[~B['out_'+c]].groupby(['tec','g','lotto'])[c].mean().reset_index(); d['cell']=d.tec+'|'+d.g.astype(str); m,rw=block_fit(d,c)
            for k,(mu,se) in lsm_se(m,rw).items(): te,g=k.split('|'); rows.append((nm,te,np.nan,int(g),np.nan,mu,se))
            LET['B_'+c]=tukey_letters(m,rw,sorted(rw))
        # ---------- micro-CT (Figg. 9-10): condizioni = tecnologia x conservazione (lotti = blocchi)
        CTV={'porosita_totale':'porosity_total','porosita_aperta':'porosity_open','DA_MIL_max_su_min':'DA','superficie_specifica_per_volume_roi_1_per_mm':'S_V_per_mm',
             'poro_spessore_mediana_um':'pore_diam_um','parete_spessore_mediana_um':'wall_thick_um','densita_connettivita_per_mm3':'conn_density'}
        for c,nm in CTV.items():
            d=R.groupby(['trattamento','tempo_gg','lotto'])[c].mean().reset_index(); d['cell']=d.trattamento+'|'+d.tempo_gg.astype(str); m,rw=block_fit(d,c)
            for k,(mu,se) in lsm_se(m,rw).items(): te,g=k.split('|'); rows.append((nm,te,np.nan,int(g),np.nan,mu,se))
            LET['CT_'+c]=tukey_letters(m,rw,sorted(rw))
        d=R.groupby(['trattamento','tempo_gg','lotto']).porosita_chiusa.mean().reset_index(); d['v']=np.log(d.porosita_chiusa*100); d['cell']=d.trattamento+'|'+d.tempo_gg.astype(str)
        m,rw=block_fit(d,'v'); LET['CT_porosita_chiusa']=tukey_letters(m,rw,sorted(rw))
        for k,(mu,se) in lsm_se(m,rw).items(): te,g=k.split('|'); rows.append(('porosity_closed_pct',te,np.nan,int(g),np.nan,float(np.exp(mu)),se))   # media geometrica; ES sulla scala log
        MEANS=pd.DataFrame(rows,columns=['variable','technology','power_pct','pellet_storage_days','tau_nominal','model_mean','standard_error'])
        MEANS.to_csv(f'{OUT_DIR}/medie_modello_ES.csv',index=False); json.dump(LET,open(f'{OUT_DIR}/lettere_tukey.json','w'),indent=1)
        print(len(MEANS),'medie ± ES salvate;', sum(len(v) for v in LET.values()),'lettere Tukey–Kramer')
        print(MEANS[(MEANS.variable=='ED')&(MEANS.tau_nominal==0.8)&(MEANS.pellet_storage_days==0)].round(3).to_string(index=False))

    # --- Original notebook cell 53 (zero-based) ---
    from statsmodels.stats.anova import anova_lm
    def bh(p):
        p=np.asarray(p,float); n=len(p); o=np.argsort(p); q=np.empty(n); prev=1.0
        for rank,i in zip(range(n,0,-1),o[::-1]): prev=min(prev,p[i]*n/rank); q[i]=prev
        return q
    if RUN_C:
        d=Mc[Mc.tn==0.8].groupby(['lotto','tecnologia','potenza','periodo']).ED.mean().reset_index(); d['P']=d.potenza.astype(str); d['G']=d.periodo.astype(str)
        print('ANOVA ED a tau = 0.8 (tecnologia x potenza x conservazione + lotto):\n', anova_lm(smf.ols('ED ~ C(tecnologia)*C(P)*C(G)+C(lotto)',data=d).fit(),typ=2)[['sum_sq','df','F','PR(>F)']].round(4).to_string())
        for ch,out in (('Lc','out_L'),('ac','out_a'),('bc','out_b')):
            c=Cc[~Cc[out]]; dd=c[c.tn==0.8].groupby(['lotto','tecnologia','potenza','periodo'])[ch].mean().reset_index(); dd['P']=dd.potenza.astype(str); dd['G']=dd.periodo.astype(str)
            a=anova_lm(smf.ols(f'{ch} ~ C(tecnologia)*C(P)*C(G)+C(lotto)',data=dd).fit(),typ=2); print(ch,'p:',a['PR(>F)'].round(3).drop('Residual').to_dict())
        res=[]
        for c in ('sigma','E','eps'):
            dd=B[~B['out_'+c]].groupby(['tec','g','lotto'])[c].mean().reset_index(); dd['G']=dd.g.astype(str)
            a=anova_lm(smf.ols(f'{c} ~ C(tec)*C(G)+C(lotto)',data=dd).fit(),typ=2); res.append((c,a.loc['C(tec)','PR(>F)'],a.loc['C(G)','PR(>F)'],a.loc['C(lotto)','PR(>F)']))
        RB=pd.DataFrame(res,columns=['grandezza','p_tecnologia','p_conservazione','p_lotto']); RB['q_tec (BH)']=bh(RB.p_tecnologia); RB['q_cons (BH)']=bh(RB.p_conservazione)
        print('\nFlessione (outlier esclusi; q = Benjamini–Hochberg tra le 3 grandezze):\n',RB.round(4).to_string(index=False))

    # --- Original notebook cell 55 (zero-based) ---
    from scipy import stats
    if RUN_C:
        CTM={'por_tot':'porosita_totale','por_open':'porosita_aperta','por_closed':'porosita_chiusa','par_med':'parete_spessore_mediana_um','poro_med':'poro_spessore_mediana_um',
             'sv_roi':'superficie_specifica_per_volume_roi_1_per_mm','cd':'densita_connettivita_per_mm3','da3d':'DA_MIL_max_su_min'}
        Lot=R.groupby(['lotto','tempo_gg','trattamento'],as_index=False)[list(CTM.values())].mean(); Lot['cond']=Lot.trattamento+Lot.tempo_gg.astype(str)
        order=['MW0','MW15','MW30','MWF0','MWF15','MWF30']; eff=[]
        for k,col in CTM.items():
            d=Lot[['cond','trattamento','tempo_gg','lotto',col]].rename(columns={col:'y'}).dropna()
            g=[d.y[d.cond==c].values for c in order if (d.cond==c).any()]; F,p=stats.f_oneway(*g); eff.append(dict(metrica=k,effetto='condizioni (6)',F=F,p=p))
            dd=d.copy(); dd['T']=dd.trattamento; dd['G']=dd.tempo_gg.astype(str); a=anova_lm(smf.ols('y ~ C(T) * C(G)',data=dd).fit(),typ=2)
            for nm,lab in (('C(T)','tecnologia'),('C(G)','tempo'),('C(T):C(G)','interazione')): eff.append(dict(metrica=k,effetto=lab,F=a.loc[nm,'F'],p=a.loc[nm,'PR(>F)']))
        E=pd.DataFrame(eff); E['q']=E.groupby('effetto').p.transform(lambda s:bh(s.values)); E.round(4).to_csv(f'{OUT_DIR}/tomo_effetti.csv',index=False)
        print(E.pivot(index='metrica',columns='effetto',values='p').round(3).to_string()); print('\nn lotti per condizione:',Lot.groupby('cond').size().reindex(order).to_dict())

    # --- Original notebook cell 57 (zero-based) ---
    IMG=['ED','Pk','Le','L','b']
    def units(pw=REF_POWER,tau=REF_TAU):
        k_=['lotto','tecnologia','periodo']
        m=Mc[(Mc.tn==tau)&(Mc.potenza==pw)].groupby(k_).ED.mean().to_frame('ED').join(Mpk[(Mpk.tn==tau)&(Mpk.potenza==pw)].groupby(k_).Pk.mean(),how='outer').join(Mle[(Mle.tn==tau)&(Mle.potenza==pw)].groupby(k_).Le.mean(),how='outer')
        c=Cc[(Cc.tn==tau)&(Cc.potenza==pw)]; L=c[~c.out_L].groupby(k_).Lc.mean().rename('L'); b=c[~c.out_b].groupby(k_).bc.mean().rename('b')
        ct=R.groupby(['lotto','trattamento','tempo_gg'])[['porosita_totale','poro_spessore_mediana_um','densita_connettivita_per_mm3']].mean(); ct.columns=['phi','pore','cd']; ct.index.names=k_
        bd=pd.concat([B[~B['out_'+k]].groupby(['lotto','tec','g'])[k].mean() for k in ('sigma','E','eps')],axis=1); bd.index.names=k_
        return m.join(L,how='outer').join(b,how='outer').join(ct,how='left').join(bd,how='left').astype(float)
    MOD={'ED':1,'Pk':1,'Le':1,'L':2,'b':2,'phi':3,'pore':3,'cd':3,'sigma':4,'E':4,'eps':4}
    def corr_table(X):
        rows=[]
        for a,b in itertools.combinations(list(MOD),2):
            if MOD[a]==MOD[b]: continue
            dd=X[[a,b]].dropna()
            if len(dd)>=5: r_,p=stats.pearsonr(dd[a],dd[b]); rows.append((a,b,len(dd),r_,p))
        T=pd.DataFrame(rows,columns=['x','y','n','r','p']); T['q_BH']=bh(T.p.values); return T
    if RUN_C:
        U=units(); print('unita totali',len(U),'| complete',len(U.dropna()))
        for lab,X0 in (('tutte le unita',U),):
            for scope in ('all','MW','MWF'):
                X=X0 if scope=='all' else X0[[i[1]==scope for i in X0.index]]; T=corr_table(X)
                top=T.reindex(T.r.abs().sort_values(ascending=False).index).head(2)
                print(f'{lab} | {scope:3s}: coppie {len(T)}, p<0.05: {int((T.p<0.05).sum())}, q<0.05 (BH): {int((T.q_BH<0.05).sum())}, min q = {T.q_BH.min():.2f}; piu forti:','; '.join(f'{x.x}-{x.y} r={x.r:.2f} (n={x.n}, p={x.p:.3f})' for x in top.itertuples()))
        CORR=corr_table(U); CORR.round(4).to_csv(f'{OUT_DIR}/correlazioni_moduli.csv',index=False)
        # surrogati leave-one-lot-out
        sg=[]
        for target in ('phi','sigma','eps'):
            best=[]
            for pr in IMG:
                dd=U[[pr,target]].dropna().reset_index(); pred=[];obs=[];base=[]
                for l in dd.lotto.unique():
                    tr,te=dd[dd.lotto!=l],dd[dd.lotto==l]
                    if len(tr)<4 or len(te)==0: continue
                    sl,ic=np.polyfit(tr[pr],tr[target],1); pred+=list(sl*te[pr]+ic); obs+=list(te[target]); base+=[tr[target].mean()]*len(te)
                obs,pred,base=map(np.array,(obs,pred,base)); best.append((pr,1-((obs-pred)**2).sum()/((obs-base)**2).sum()))
            best.sort(key=lambda x:-x[1]); sg.append((target,best[0][0],best[0][1]))
        print('\nSurrogati leave-one-lot-out (miglior predittore da immagine):',[(t,p,round(r,2)) for t,p,r in sg])
        # bilancio di massa e Gibson-Ashby
        ct=R.groupby(['lotto','trattamento','tempo_gg']).porosita_totale.mean(); ct.index.names=['lotto','tec','g']
        m_=Mc[(Mc.tn==REF_TAU)&(Mc.potenza==REF_POWER)].groupby(['lotto','tecnologia','periodo']).VEI.mean(); m_.index.names=['lotto','tec','g']
        J=pd.concat([m_,ct],axis=1,join='inner'); J.columns=['VEI','phi']; J['p0']=1-1/J.VEI; J['p1']=1-0.9/J.VEI      # perdita di massa 0 e 10 %
        print('Bilancio di massa (porosita misurata vs porosita da VEI con perdita di massa 0-10 %):',{t:(round(J.xs(t,level=1).phi.mean(),2),round(J.xs(t,level=1).p0.mean(),2),round(J.xs(t,level=1).p1.mean(),2)) for t in ('MW','MWF')},'| r = %.2f'%np.corrcoef(J.phi,(J.p0+J.p1)/2)[0,1])
        bl=pd.concat([B[~B['out_'+k]].groupby(['lotto','tec','g'])[k].mean() for k in ('sigma','E')],axis=1); GA=pd.concat([ct.rename('phi'),bl],axis=1,join='inner'); GA['rho']=1-GA.phi
        for c in ('E','sigma'):
            sl,ic,rr,p,se=stats.linregress(np.log(GA.rho),np.log(GA[c])); print(f'Gibson–Ashby {c}: esponente {sl:.2f} ± {se:.2f}, p = {p:.3f}, n = {len(GA)}')

    # --- Original notebook cell 59 (zero-based) ---
    from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
    from scipy.spatial.distance import squareform
    if RUN_C:
        Un=U.rename(columns={'L':'L*','b':'b*','phi':'porosity','pore':'pore size','cd':'connectivity','sigma':'stress','E':'modulus','eps':'strain'})
        Uc=Un.dropna(); X=Uc.values; Z=(X-X.mean(0))/X.std(0,ddof=1); n,p=Z.shape
        Uu,Ss,Vt=np.linalg.svd(Z,full_matrices=False); ev=Ss**2/(n-1); expl=ev/ev.sum(); load=Vt.T*np.sqrt(ev); scores=Uu*Ss; names=list(Uc.columns)
        print(f'unita complete n = {n}, variabili p = {p} | varianza spiegata PC1-PC3 (%):',(expl[:3]*100).round(1))
        for k in (0,1): print(f'PC{k+1} carichi maggiori:',{names[i]:round(load[i,k],2) for i in np.argsort(-np.abs(load[:,k]))[:5]})
        lab=[f'{l} {t} {g} d' for (l,t,g) in Uc.index]; Lk=linkage(Z,'ward'); rr=np.corrcoef(Z.T); Lv=linkage(squareform(1-np.abs(rr),checks=False),'average')
        print('cluster (3) delle unita:',dict(zip(lab,fcluster(Lk,3,'maxclust'))))
        pd.DataFrame(load[:,:3],index=names,columns=['PC1','PC2','PC3']).round(3).to_csv(f'{OUT_DIR}/pca_carichi.csv')
        TECC={'MW':'#2F6DB5','MWF':'#D9772B'}; MK={0:'o',15:'s',30:'^'}
        fig=plt.figure(figsize=(8.5,9),constrained_layout=True); gs=fig.add_gridspec(2,2,height_ratios=[1.15,1]); ax=fig.add_subplot(gs[0,:])
        ax.add_patch(plt.Circle((0,0),1,fill=False,color='#9BC53D',lw=.8))
        for i,nm in enumerate(names):
            ax.annotate('',xy=(load[i,0],load[i,1]),xytext=(0,0),arrowprops=dict(arrowstyle='-',color='#1d4e89',lw=.9)); ax.text(load[i,0]*1.04,load[i,1]*1.04,nm,fontsize=7,color='#1d4e89')
        sc=scores/np.sqrt(ev)/np.abs(scores/np.sqrt(ev)).max()*0.9
        for (l,t,g),(a_,b_) in zip(Uc.index,sc[:,:2]): ax.plot(a_,b_,MK[int(g)],ms=5,color=TECC[t],mfc=TECC[t] if t=='MW' else 'white')
        ax.axhline(0,color='#bbb',lw=.6); ax.axvline(0,color='#bbb',lw=.6); ax.set_aspect('equal'); ax.set_xlabel(f'PC1 ({expl[0]*100:.1f}%)'); ax.set_ylabel(f'PC2 ({expl[1]*100:.1f}%)')
        ax.legend(handles=[plt.Line2D([],[],marker=MK[g],ls='',color='#555',label=f'{g} d') for g in (0,15,30)]+[plt.Line2D([],[],marker='o',ls='',color=TECC['MW'],label='MW'),plt.Line2D([],[],marker='o',ls='',color=TECC['MWF'],mfc='white',label='MWF')],frameon=False,fontsize=7,loc='lower left')
        ax2=fig.add_subplot(gs[1,0]); dendrogram(Lk,labels=lab,orientation='right',ax=ax2,color_threshold=0,above_threshold_color='#555',leaf_font_size=6); ax2.set_xlabel('Ward distance')
        ax3=fig.add_subplot(gs[1,1]); dendrogram(Lv,labels=names,orientation='right',ax=ax3,color_threshold=0,above_threshold_color='#555',leaf_font_size=7); ax3.set_xlabel('1 − |r|')
        fig.savefig(f'{OUT_DIR}/PCA_HCA.png',dpi=200); plt.close("all")

    # --- Original notebook cell 61 (zero-based) ---
    if RUN_C:
        fig,axs=plt.subplots(2,3,figsize=(10,5.5),sharey=True,constrained_layout=True)
        colp={40:'#9CBDE3',60:'#4B86C5',80:'#1B4A86'}; colw={40:'#F2C69D',60:'#E58E45',80:'#A9531A'}
        for i,tec in enumerate(('MW','MWF')):
            for j,per in enumerate((0,15,30)):
                ax=axs[i,j]; Mx=MEANS[(MEANS.variable=='ED')&(MEANS.technology==tec)&(MEANS.pellet_storage_days==per)]
                for pw,g in Mx.groupby('power_pct'):
                    col=(colp if tec=='MW' else colw)[pw]; ax.errorbar(g.tau_nominal,g.model_mean,g.standard_error,fmt='o',ms=4,color=col,capsize=2,label=f'{pw} %')
                    k_=KIN[(KIN.tecnologia==tec)&(KIN.potenza==pw)&(KIN.periodo==per)].iloc[0]; tt=np.linspace(0,1,100); ax.plot(tt,ed_kin(tt,k_.ED_inf,k_.k),color=col,lw=1)
                ax.set_title(f'{tec}, {per} d'); ax.set_xlabel('τ'); ax.legend(frameon=False,fontsize=7,loc='upper left')
            axs[i,0].set_ylabel('ED')
        fig.savefig(f'{OUT_DIR}/cinetica_ED.png',dpi=200); plt.close("all")

    # --- Original notebook cell 63 (zero-based) ---
    if RUN_C:
        with pd.ExcelWriter(f'{OUT_DIR}/risultati_analisi.xlsx') as xw:
            OUT.to_excel(xw,'Outliers',index=False); KIN.round(4).to_excel(xw,'Kinetics_ED',index=False); MEANS.to_excel(xw,'Model_means_SE',index=False)
            E.round(4).to_excel(xw,'ANOVA_microCT',index=False); CORR.round(4).to_excel(xw,'Correlations',index=False)
            pd.DataFrame([(k,c,l) for k,v in LET.items() for c,l in v.items()],columns=['family','condition','letters']).to_excel(xw,'Tukey_letters',index=False)
            pd.DataFrame(load[:,:3],index=names,columns=['PC1','PC2','PC3']).round(3).to_excel(xw,'PCA_loadings')
        print('scritto', f'{OUT_DIR}/risultati_analisi.xlsx')
    return {"units": len(U), "complete_units": len(U.dropna()), "correlations": len(CORR), "significant_q": int((CORR.q_BH < .05).sum())}

def compare_ct_blocks(csv_path):
    """Compare original C5 model with additive lot block (not a replacement)."""
    import statsmodels.formula.api as smf
    from statsmodels.stats.anova import anova_lm
    metrics = ['porosita_totale','porosita_aperta','porosita_chiusa','parete_spessore_mediana_um','poro_spessore_mediana_um','superficie_specifica_per_volume_roi_1_per_mm','densita_connettivita_per_mm3','DA_MIL_max_su_min']
    df = pd.read_csv(csv_path)
    df = df[df.trattamento.isin(['MW','MWF'])].groupby(['lotto','tempo_gg','trattamento'],as_index=False)[metrics].mean()
    records=[]
    for metric in metrics:
        d = df[['lotto','tempo_gg','trattamento',metric]].dropna().rename(columns={metric:'y'})
        d['T']=d.trattamento; d['G']=d.tempo_gg.astype(str)
        for model, formula in [('legacy','y ~ C(T)*C(G)'), ('lot_block','y ~ C(T)*C(G)+C(lotto)')]:
            fit=smf.ols(formula,d).fit(); a=anova_lm(fit,typ=2)
            rank=int(np.linalg.matrix_rank(fit.model.exog)); ncols=fit.model.exog.shape[1]
            for effect in ['C(T)','C(G)','C(T):C(G)']:
                records.append(dict(metric=metric,model=model,effect=effect,n=len(d),rank=rank,n_columns=ncols,df_resid=fit.df_resid,F=a.loc[effect,'F'],p=a.loc[effect,'PR(>F)']))
    out=pd.DataFrame(records)
    from statsmodels.stats.multitest import multipletests
    out['q_BH']=out.groupby(['model','effect']).p.transform(lambda x: multipletests(x,method='fdr_bh')[1] if x.notna().all() else np.full(len(x),np.nan))
    return out

