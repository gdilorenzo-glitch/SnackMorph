"""VOX algorithms and original settings. The default sampling step is 3 as in cell 23; callers must explicitly choose a step."""
import numpy as np
#@title 2) PARAMETRI { display-mode: "form" }

#@markdown ### Cartelle (su Drive)
#@markdown Cartella che contiene i VOX (anche in sottocartelle). OUTPUT_ROOT vuoto = ROOT_DIR/_analisi.
ROOT_DIR = "/content/drive/MyDrive/microCT"        #@param {type:"string"}
OUTPUT_ROOT = ""                                   #@param {type:"string"}
VOX_PATTERN = "*.vox"                              #@param {type:"string"}
RECURSIVE = True                                   #@param {type:"boolean"}
EXCLUDE_DIRS = "_analisi,_vox_tmp"                 #@param {type:"string"}
#@markdown Elabora solo i file il cui nome contiene questo testo (vuoto = tutti).
FILE_FILTER = ""                                   #@param {type:"string"}
OVERWRITE = False                                  #@param {type:"boolean"}
#@markdown Copia il file su disco locale prima di leggerlo (utile con la modalita' "ogni N" su Drive lento).
COPY_TO_LOCAL = False                              #@param {type:"boolean"}

#@markdown ### Impostazioni dal file XML (stessa cartella e stesso nome del VOX)
USE_XML = True                                     #@param {type:"boolean"}
#@markdown Se REQUIRE_XML e' attivo, i file senza XML vengono saltati; altrimenti si usa l'intestazione del VOX o i valori manuali.
REQUIRE_XML = False                                #@param {type:"boolean"}
#@markdown Valori manuali, usati solo se mancano XML e intestazione. Forma come stack,height,width.
MANUAL_SHAPE_ZYX = ""                              #@param {type:"string"}
MANUAL_DTYPE = "uint16"                            #@param ["uint8", "uint16", "int16", "float32"]
MANUAL_VOXEL_UM = 0                                #@param {type:"number"}
BYTE_ORDER = "little"                              #@param ["little", "big"]
HEADER_BYTES = "auto"                              #@param {type:"string"}

#@markdown ### 1) Campionamento
#@markdown "media" conserva meglio le pareti sottili (legge tutte le slice); "ogni N" e' piu' rapido ma puo' perderle.
SAMPLING_MODE = "media"                            #@param ["media", "ogni N"]
#@markdown Passo fisso su X, Y e Z (0 = automatico: voxel ridotto vicino a TARGET_VOXEL_UM, e volume ridotto non oltre MAX_REDUCED_VOXELS_M milioni di voxel).
SAMPLING_STEP = 0                                  #@param {type:"integer"}
TARGET_VOXEL_UM = 27                               #@param {type:"number"}
MAX_REDUCED_VOXELS_M = 300                         #@param {type:"integer"}
SAVE_REDUCED_VOX = False                           #@param {type:"boolean"}
#@markdown Memoria: True = usa edt (distanze) e SimpleITK (massimi h) al posto di scipy e scikit-image in questi due passaggi (stessi risultati, circa un decimo della RAM); False = solo scipy e scikit-image.
USE_FAST_LIBS = True                               #@param {type:"boolean"}

#@markdown ### 2) ROI (algoritmo; raggi in pixel della griglia di lavoro della ROI)
#@markdown La ROI si calcola su una griglia con il lato lungo di circa ROI_WORKING_SIZE pixel (0 = griglia del volume ridotto).
ROI_WORKING_SIZE = 512             #@param {type:"integer"}
ROI_STEP = 4                       #@param {type:"integer"}
ROI_SMOOTH_Z = 5                   #@param {type:"integer"}
T1_MANUAL = 0.0                    #@param {type:"number"}
T2_MANUAL = 0.0                    #@param {type:"number"}
SIGMA = 1.2                        #@param {type:"number"}
GLUE_MARGIN = 1                    #@param {type:"integer"}
WEDGE_MARGIN = 2                   #@param {type:"integer"}
WEDGE_OPEN = 12                    #@param {type:"integer"}
TOPHAT_R = 10                      #@param {type:"integer"}
K_LOW = 4.0                        #@param {type:"number"}
K_HIGH = 10.0                      #@param {type:"number"}
CLOSE_R = 6                        #@param {type:"integer"}
#@markdown Pixel aggiunti attorno al contorno esterno del campione (include l'ultimo strato di parete).
OUTER_MARGIN = 1                   #@param {type:"integer"}
#@markdown Raggio (px) di chiusura per riconoscere le cavita' interne racchiuse (es. il vuoto centrale di un estruso tubolare chiuso): le include nella ROI. 0 = non includerle.
CAVITY_CLOSE_R = 15                #@param {type:"integer"}
MIN_AREA = 500                     #@param {type:"integer"}
ATTACH_DIST = 40                   #@param {type:"integer"}
ATTACH_MIN_AREA = 60               #@param {type:"integer"}
SAVE_ROI = True                    #@param {type:"boolean"}
N_QC = 6                           #@param {type:"integer"}
#@markdown Una slice e' segnalata se la sua area si discosta di oltre ANOMALY_TOL dalla mediana mobile (finestra ANOMALY_WINDOW slice): i cambi graduali lungo il campione non vengono segnalati.
ANOMALY_TOL = 0.25                 #@param {type:"number"}
ANOMALY_WINDOW = 31                #@param {type:"integer"}

#@markdown ### 3) Analisi: volume di lavoro e segmentazione pori / materiale
#@markdown ANALYSIS_DS riduce ancora il volume ridotto (1 = nessuna riduzione). Il voxel di analisi e' VOXEL_SIZE_UM x passo di campionamento x ANALYSIS_DS.
ANALYSIS_DS = 1                    #@param {type:"integer"}
PAD_VOXELS = 6                     #@param {type:"integer"}
#@markdown Soglia in unita' di grigio del volume: 0 = automatica (Otsu sui voxel della ROI).
THRESHOLD = 0.0                    #@param {type:"number"}
SEG_SIGMA = 1.0                    #@param {type:"number"}
MIN_OBJECT_VOXELS = 8              #@param {type:"integer"}
CONNECTIVITY = 1                   #@param [1, 3]

#@markdown ### 3) Analisi: cosa calcolare
COMPUTE_THICKNESS = True           #@param {type:"boolean"}
COMPUTE_PORE_OBJECTS = True        #@param {type:"boolean"}
COMPUTE_ANISOTROPY = True          #@param {type:"boolean"}
RUN_3D = True                      #@param {type:"boolean"}
RUN_2D = True                      #@param {type:"boolean"}
PSD_LEVELS = 20                    #@param {type:"integer"}
#@markdown Classi di spessore in micrometri (separate da virgola).
WALL_CLASSES_UM = "50,200,400"     #@param {type:"string"}
PORE_CLASSES_UM = "550,1150"       #@param {type:"string"}
WATERSHED_H = 1.0                  #@param {type:"number"}
MIN_PORE_VOXELS = 20               #@param {type:"integer"}
MAX_PORES_GEOMETRY = 3000          #@param {type:"integer"}
FERET_DIRECTIONS = 60              #@param {type:"integer"}
N_DIRECTIONS = 200                 #@param {type:"integer"}

#@markdown ### 3) Analisi 2D sui piani X, Y, Z
#@markdown Passo tra le slice in slice ORIGINALI (3 = una ogni 3): si arrotonda al passo del volume di analisi.
STEP_2D = 3                        #@param {type:"integer"}
PLANES = "x,y,z"                   #@param {type:"string"}
MIN_PORE_PIXELS_2D = 6             #@param {type:"integer"}
EXCLUDE_EDGE_PORES_2D = False      #@param {type:"boolean"}

#@markdown ### Cosa eseguire
RUN_LIST = True                    #@param {type:"boolean"}
RUN_PREVIEW = False                #@param {type:"boolean"}
PREVIEW_FILE_INDEX = 0             #@param {type:"integer"}
RUN_BATCH = True                   #@param {type:"boolean"}
RUN_ANALYSIS = True                #@param {type:"boolean"}
SAVE_FIGURES = True                #@param {type:"boolean"}
#@markdown ### Esempi visivi su alcune slice (per controllare segmentazione e spessori)
GLUE_MIN_AREA = 64
WEDGE_REC_MIN_R = 2
WEDGE_INNER_OPEN_R = 2
WEDGE_CLOSE_MIN_R = 3
CAND_OPEN_R = 1
ROI_OPEN_R = 2
CAVITY_NEAR_R = 3
WATERSHED_SIGMA = 1.0
GEOMETRY_MIN_VOXELS = 10
SURFACE_EROSION = 2
SURFACE_SIGMA = 0.8
MIN_ROI_PIXELS_2D = 50
SAVE_EXAMPLES = True               #@param {type:"boolean"}
N_EXAMPLE_SLICES = 4               #@param {type:"integer"}
ROOT_DIR="."
OUTPUT_ROOT=""
SAMPLING_STEP=3
RUN_LIST=RUN_BATCH=RUN_PREVIEW=False
# --- Original notebook cell 25 (zero-based) ---
import os, glob, math, time, shutil, csv, fnmatch, re, traceback
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation
from scipy.spatial import ConvexHull
import gc
from inspect import signature

# Preserve the historical strict size threshold across scikit-image versions.
_REMOVE_SMALL_OBJECTS_HAS_MAX_SIZE = "max_size" in signature(morphology.remove_small_objects).parameters

def _remove_small_objects_legacy(mask, min_size):
    """Remove connected components with fewer than min_size elements."""
    if min_size <= 1:
        return mask.copy()
    if _REMOVE_SMALL_OBJECTS_HAS_MAX_SIZE:
        return morphology.remove_small_objects(mask, max_size=min_size - 1)
    return morphology.remove_small_objects(mask, min_size=min_size)
try:
    import edt as _edt_mod
except ImportError:
    _edt_mod = None
if not USE_FAST_LIBS:
    _edt_mod = None

try:
    import SimpleITK as _sitk
except ImportError:
    _sitk = None
if not USE_FAST_LIBS:
    _sitk = None

def _h_maxima(img, h):
    """Massimi h (stesso risultato di skimage.morphology.h_maxima) con la ricostruzione di SimpleITK: molto meno memoria e piu' veloce."""
    if _sitk is not None:
        try:
            h32 = np.float32(h)
            if float(h) > float(np.ptp(img)):
                return np.zeros(img.shape, np.uint8)
            a = _sitk.GetImageFromArray(np.ascontiguousarray(img - h32)); b = _sitk.GetImageFromArray(np.ascontiguousarray(img, dtype=np.float32))
            rec = _sitk.ReconstructionByDilation(a, b, True); del a, b           # True = connettivita' completa (26 vicini), come skimage
            r = _sitk.GetArrayFromImage(rec); del rec
            np.subtract(img, r, out=r)
            return (r >= h32).astype(np.uint8)
        except Exception:
            pass
    return morphology.h_maxima(img, h)

def _medial_axis(mat2):
    """Asse mediano 2D con seme fisso (senza seme il risultato cambia leggermente da una esecuzione all'altra)."""
    for kw in ({'rng': 0}, {'random_state': 0}, {}):
        try:
            return morphology.medial_axis(mat2, return_distance=True, **kw)
        except TypeError:
            continue

def _edt32(mask):
    """Distanza euclidea dal piu' vicino voxel falso, in float32 (scipy la darebbe in float64: il doppio della memoria).
    Con il pacchetto edt il risultato e' lo stesso; senza, si usa scipy."""
    if _edt_mod is not None:
        try:
            return _edt_mod.edt(np.ascontiguousarray(mask, dtype=bool), black_border=False, parallel=0)
        except Exception:
            pass
    return ndi.distance_transform_edt(mask).astype(np.float32)

DTYPE_MAP = {'word': 'uint16', 'byte': 'uint8', 'short': 'int16', 'int': 'int32', 'long': 'int32', 'dword': 'uint32', 'float': 'float32'}

def output_root():
    return OUTPUT_ROOT.strip() or os.path.join(ROOT_DIR, '_analisi')

def discover_files():
    """Tutti i VOX in ROOT_DIR (e sottocartelle), esclusi le cartelle di uscita e i VOX ridotti salvati dalla pipeline."""
    pats = [p.strip().lower() for p in VOX_PATTERN.split(',') if p.strip()]
    excl = {x.strip() for x in EXCLUDE_DIRS.split(',') if x.strip()} | {os.path.basename(output_root().rstrip('/'))}
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        dirnames[:] = [d for d in dirnames if d not in excl and not d.startswith('.')] if RECURSIVE else []
        for fn in filenames:
            low = fn.lower()
            if any(fnmatch.fnmatch(low, p) for p in pats) and not re.search(r'_s\d+(x\d+x\d+)?\.vox$', low):
                if FILE_FILTER and FILE_FILTER.lower() not in low:
                    continue
                found.append(os.path.join(dirpath, fn))
    return sorted(found)

def parse_xml(path):
    """Legge un XML 'data_info': restituisce le impostazioni e tutti gli attributi appiattiti come xml_<tag>_<attributo>."""
    import xml.etree.ElementTree as ET
    with open(path, 'rb') as fh:
        txt = fh.read().decode('utf-8-sig', errors='replace')
    root = ET.fromstring(txt.encode('utf-8'))
    meta = {}
    for el in root.iter():
        for k, v in el.attrib.items():
            meta[f'xml_{el.tag}_{k}'] = v
    vol = root.find('.//volume')
    st = dict(meta=meta)
    if vol is not None:
        a = vol.attrib
        if all(k in a for k in ('width', 'height', 'stack')):
            st['shape'] = (int(a['stack']), int(a['height']), int(a['width']))
        st['dtype'] = DTYPE_MAP.get(str(a.get('type', 'word')).lower())
        st['type'] = a.get('type')
        st['pitch'] = float(a['pitch']) if a.get('pitch') else None
        st['vox_name'] = os.path.basename(str(a.get('path', '')).replace('\\', '/'))
    rg = root.find('.//range')
    if rg is not None:
        try:
            st['range'] = (float(rg.attrib['min']), float(rg.attrib['max']))
        except Exception:
            pass
    return st

def find_xml(vox_path):
    """XML della stessa cartella: stesso nome del VOX; altrimenti quello il cui <volume path> indica il VOX; altrimenti l'unico XML se c'e' un solo VOX."""
    d = os.path.dirname(vox_path); stem = os.path.splitext(os.path.basename(vox_path))[0].lower(); name = os.path.basename(vox_path).lower()
    xmls = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith('.xml')]
    for x in xmls:
        if os.path.splitext(os.path.basename(x))[0].lower() == stem:
            return x
    for x in xmls:
        try:
            if parse_xml(x).get('vox_name', '').lower() == name:
                return x
        except Exception:
            pass
    voxes = [f for f in os.listdir(d) if f.lower().endswith('.vox')]
    if len(xmls) == 1 and len(voxes) == 1:
        return xmls[0]
    return None

def read_vox_header(path):
    """Intestazione XML incorporata nel VOX (se c'e')."""
    with open(path, 'rb') as fh:
        head = fh.read(4096)
    i = head.find(b'<volume')
    if i < 0:
        return None
    txt = head[i:i + 1000].decode('latin-1')
    g = lambda k: (re.search(k + r'\s*=\s*"?([^"\s>]+)', txt) or [None, None])[1]
    t, w, h, s, p = g('type'), g('width'), g('height'), g('stack'), g('pitch')
    if not (w and h and s):
        return None
    return dict(shape=(int(s), int(h), int(w)), dtype=DTYPE_MAP.get((t or 'word').lower()), pitch=float(p) if p else None, type=t)

def resolve_settings(vox_path):
    """Impostazioni di un VOX: XML > intestazione del VOX > valori manuali. Restituisce un dizionario con 'origine' e i metadati."""
    st = dict(shape=None, dtype=None, pitch=None, range=None, origine=None, xml=None, meta={})
    xml = find_xml(vox_path) if USE_XML else None
    if xml:
        try:
            x = parse_xml(xml)
            st.update(shape=x.get('shape'), dtype=x.get('dtype'), pitch=x.get('pitch'), range=x.get('range'), meta=x['meta'], xml=xml, origine='xml')
        except Exception as e:
            print(f"  XML non leggibile ({os.path.basename(xml)}): {e}")
    if REQUIRE_XML and not xml:
        raise FileNotFoundError("nessun file XML trovato accanto al VOX (REQUIRE_XML attivo)")
    if st['shape'] is None or st['dtype'] is None or not st['pitch']:
        h = read_vox_header(vox_path)
        if h:
            for k in ('shape', 'dtype', 'pitch'):
                if not st[k]:
                    st[k] = h[k]
            st['origine'] = (st['origine'] + '+intestazione VOX') if st['origine'] else 'intestazione VOX'
    if st['shape'] is None and MANUAL_SHAPE_ZYX.strip():
        st['shape'] = tuple(int(v) for v in MANUAL_SHAPE_ZYX.replace(' ', '').split(',')); st['origine'] = (st['origine'] + '+manuale') if st['origine'] else 'manuale'
    if st['dtype'] is None:
        st['dtype'] = MANUAL_DTYPE
    if not st['pitch'] and MANUAL_VOXEL_UM:
        st['pitch'] = float(MANUAL_VOXEL_UM)
    missing = [k for k in ('shape', 'pitch') if not st[k]]
    if missing:
        raise ValueError(f"impostazioni mancanti ({', '.join(missing)}): nessun XML utile, nessuna intestazione nel VOX e nessun valore manuale")
    return st

def open_volume(vox_path, st):
    """Apre il VOX come VoxReader con le impostazioni risolte; verifica la coerenza con la dimensione del file."""
    shape = tuple(st['shape'])
    dt = np.dtype(st['dtype']).newbyteorder('<' if BYTE_ORDER == 'little' else '>')
    n = int(np.prod(shape, dtype=np.int64)) * dt.itemsize
    size = os.path.getsize(vox_path)
    offset = size - n if str(HEADER_BYTES).strip().lower() == 'auto' else int(HEADER_BYTES)
    if offset < 0 or offset + n > size:
        raise ValueError(f"il file pesa {size/1e9:.3f} GB ma {shape} x {dt.itemsize} byte ({st['origine']}) richiedono {n/1e9:.3f} GB: "
                         "controlla che XML e VOX appartengano allo stesso volume, oppure DTYPE e BYTE_ORDER")
    r = VoxReader(vox_path, shape, dt, offset); r.pitch = float(st['pitch'])
    r.header_bytes = offset
    return r

def choose_step(shape, pitch):
    """Passo di campionamento: fisso, oppure il piu' piccolo che porta il voxel vicino al valore obiettivo senza superare la memoria."""
    if SAMPLING_STEP > 0:
        return int(SAMPLING_STEP)
    n = max(1, int(round(TARGET_VOXEL_UM / pitch)))
    while (shape[0] // n) * (shape[1] // n) * (shape[2] // n) > MAX_REDUCED_VOXELS_M * 1e6:
        n += 1
    return n

class VoxReader:
    """Volume (Z,Y,X) letto una slice alla volta con letture sequenziali (molto piu' veloce di memmap su Drive)."""
    def __init__(self, path, shape, dtype, offset):
        self.path, self.shape, self.dtype, self.offset = path, shape, np.dtype(dtype), int(offset)
        self.slice_bytes = shape[1] * shape[2] * self.dtype.itemsize
    def __getitem__(self, z):
        if not isinstance(z, (int, np.integer)):
            raise TypeError("VoxReader supporta solo l'indice di una slice")
        a = np.fromfile(self.path, dtype=self.dtype, count=self.shape[1] * self.shape[2], offset=self.offset + int(z) * self.slice_bytes)
        return a.reshape(self.shape[1], self.shape[2])

def maybe_local(path):
    if COPY_TO_LOCAL and path.startswith('/content/drive'):
        tmpdir = '/content/_vox_tmp'; os.makedirs(tmpdir, exist_ok=True)
        dst = os.path.join(tmpdir, os.path.basename(path))
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
            total = os.path.getsize(path); t0 = time.time(); done = 0; last = 0
            print(f"  copio su disco locale ({total/1e9:.1f} GB)...", flush=True)
            with open(path, 'rb') as fi, open(dst, 'wb') as fo:
                while True:
                    buf = fi.read(64 * 1024 * 1024)
                    if not buf:
                        break
                    fo.write(buf); done += len(buf)
                    if done - last >= 1_000_000_000:
                        last = done
                        print(f"   copiati {done/1e9:.1f}/{total/1e9:.1f} GB  ({done/1e6/max(time.time()-t0,1e-6):.0f} MB/s)", flush=True)
            print(f"  copia fatta in {time.time()-t0:.0f}s", flush=True)
        return dst, True
    return path, False

def read_speed_test(vol, mode, sz):
    """Legge alcune slice e stima il tempo totale di lettura: se e' lungo, suggerisce la copia in locale."""
    Z = vol.shape[0]; n_total = (Z // sz) if mode != 'media' else Z
    idx = np.linspace(0, Z - 1, 4).astype(int)
    t0 = time.time()
    for z in idx:
        _ = vol[int(z)]
    per = (time.time() - t0) / len(idx)
    mb = vol.slice_bytes / 1e6 if hasattr(vol, 'slice_bytes') else float(np.asarray(vol[0]).nbytes) / 1e6
    eta = per * n_total
    print(f"   lettura: {per:.2f} s per slice ({mb/max(per,1e-6):.0f} MB/s) -> stima {eta/60:.1f} min per leggere {n_total} slice", flush=True)
    if eta > 300:
        print("   ATTENZIONE: lettura lenta. Copia prima il file su disco locale (COPY_TO_LOCAL = True) oppure da una cella: "
              "!rsync -ah --progress <file su Drive> /content/", flush=True)
    return eta

def _block_mean_xy(a, sy, sx):
    Y, X = a.shape
    Yc, Xc = (Y // sy) * sy, (X // sx) * sx
    return a[:Yc, :Xc].reshape(Yc // sy, sy, Xc // sx, sx).mean((1, 3))

def sample_volume(vol, mode, sz, sy, sx):
    """Volume ridotto (nz, ny, nx), in memoria, dello stesso tipo del volume di partenza."""
    Z, Y, X = vol.shape
    nz, ny, nx = Z // sz, Y // sy, X // sx
    if nz * ny * nx > 450_000_000:
        raise MemoryError(f"Volume ridotto troppo grande ({nz}x{ny}x{nx}): aumenta SAMPLING_STEP")
    dt = np.dtype(vol.dtype).newbyteorder('=')
    out = np.zeros((nz, ny, nx), dtype=dt)
    info = np.iinfo(dt) if np.issubdtype(dt, np.integer) else None
    t0 = time.time()
    for k in range(nz):
        if mode == 'media':
            acc = np.zeros((ny, nx), np.float32)
            for z in range(k * sz, k * sz + sz):
                acc += _block_mean_xy(np.asarray(vol[z], dtype=np.float32), sy, sx)[:ny, :nx]
            acc /= sz
            out[k] = np.clip(np.rint(acc), info.min, info.max).astype(dt) if info else acc.astype(dt)
        else:
            out[k] = np.asarray(vol[k * sz])[:ny * sy:sy, :nx * sx:sx]
        if k % max(nz // 10, 1) == 0:
            print(f"   campionamento {k}/{nz}  ({time.time()-t0:.0f}s)", flush=True)
    return out

def write_vox(path, vol, pitch_um):
    """Scrive un .vox con intestazione XML seguita dai dati grezzi little endian."""
    nz, ny, nx = vol.shape
    typ = {'uint8': 'byte', 'uint16': 'word', 'int16': 'short', 'float32': 'float'}.get(np.dtype(vol.dtype).name, 'word')
    header = f'<volume type="{typ}" width="{nx}" height="{ny}" stack="{nz}" pitch="{pitch_um:.6f}">\n'.encode()
    with open(path, 'wb') as fh:
        fh.write(header)
        for k in range(nz):
            fh.write(np.ascontiguousarray(vol[k]).astype(np.dtype(vol.dtype).newbyteorder('<')).tobytes())


def describe_files(files):
    """Tabella delle impostazioni di ogni file, senza leggere i volumi."""
    rows = []
    root = ROOT_DIR.rstrip('/')
    for f in files:
        r = dict(cartella=os.path.relpath(os.path.dirname(f), root), file=os.path.basename(f), dimensione_gb=round(os.path.getsize(f) / 1e9, 3))
        try:
            st = resolve_settings(f)
            n = choose_step(st['shape'], st['pitch'])
            Z, Y, X = st['shape']
            r.update(impostazioni=st['origine'], xml=os.path.basename(st['xml']) if st['xml'] else '', dimensioni_zyx='x'.join(map(str, st['shape'])), tipo=st['dtype'],
                     pitch_um=st['pitch'], passo=n, voxel_ridotto_um=round(st['pitch'] * n, 2), volume_ridotto='x'.join(map(str, (Z // n, Y // n, X // n))),
                     ridotto_MB=round((Z // n) * (Y // n) * (X // n) * 2 / 1e6))
            try:
                nbytes = int(np.prod(st['shape'], dtype=np.int64)) * np.dtype(st['dtype']).itemsize
                r['coerenza_dimensione'] = 'ok' if os.path.getsize(f) >= nbytes else 'file troppo piccolo'
            except Exception:
                pass
        except Exception as e:
            r['errore'] = str(e)
        rows.append(r)
    return pd.DataFrame(rows)

def done_path(out_dir, base):
    return os.path.join(out_dir, base + '_riepilogo.csv')

def out_dir_for(f):
    rel = os.path.relpath(os.path.dirname(f), ROOT_DIR.rstrip('/'))
    base = os.path.splitext(os.path.basename(f))[0]
    return os.path.normpath(os.path.join(output_root(), rel, base)), base

# --- Original notebook cell 27 (zero-based) ---
def roi_params():
    return dict(sigma=SIGMA, glue_margin=GLUE_MARGIN, wedge_margin=WEDGE_MARGIN, wedge_open=WEDGE_OPEN, tophat_r=TOPHAT_R,
                k_low=K_LOW, k_high=K_HIGH, close_r=CLOSE_R, min_area=MIN_AREA, attach_dist=ATTACH_DIST, attach_min_area=ATTACH_MIN_AREA,
                t1=(T1_MANUAL or None), t2=(T2_MANUAL or None), outer_margin=OUTER_MARGIN, cavity_close_r=CAVITY_CLOSE_R)

def roi_ds(shape):
    """Fattore di sottocampionamento della griglia di lavoro della ROI (lato lungo ~ ROI_WORKING_SIZE pixel)."""
    if ROI_WORKING_SIZE <= 0:
        return 1
    return max(1, int(round(max(shape[1], shape[2]) / ROI_WORKING_SIZE)))

def auto_thresholds(gs):
    t1, t2 = filters.threshold_multiotsu(gs, classes=3)
    return float(t1), float(t2)

def make_roi_slice(img, **p):
    gs = ndi.gaussian_filter(np.asarray(img, dtype=np.float32), p['sigma'])
    t1, t2 = p.get('t1'), p.get('t2')
    if t1 is None or t2 is None:
        a, b = auto_thresholds(gs)
        t1 = a if t1 is None else t1
        t2 = b if t2 is None else t2
    # colla = classe piu' attenuante
    glue = _remove_small_objects_legacy(gs > t2, GLUE_MIN_AREA)
    glue_d = ndi.binary_dilation(glue, morphology.disk(p['glue_margin'])) if p['glue_margin'] > 0 else glue
    # cuneo = grande regione omogenea di grigio medio, regolarizzata con l'inviluppo convesso (indipendente dall'orientamento)
    mid = (gs > t1) & (gs <= t2)
    mid_o = morphology.opening(mid, morphology.disk(p['wedge_open']))
    lab = measure.label(mid_o)
    wedge = np.zeros_like(mid)
    if lab.max() > 0:
        big = max(measure.regionprops(lab), key=lambda r: r.area)
        seed = lab == big.label
        tol = max(WEDGE_REC_MIN_R, int(0.6 * p['wedge_open']))                 # il bordo si recupera solo entro tol px dal nucleo
        zone = ndi.binary_dilation(seed, morphology.disk(tol))
        rec = morphology.reconstruction(seed.astype(np.uint8), (mid & zone).astype(np.uint8), method='dilation').astype(bool)
        wedge = morphology.opening(ndi.binary_fill_holes(rec), morphology.disk(WEDGE_INNER_OPEN_R))
        wedge = ndi.binary_fill_holes(morphology.closing(wedge, morphology.disk(max(WEDGE_CLOSE_MIN_R, p['wedge_open']))))   # colma le tacche dovute all'alone vicino alla colla
    wedge_d = ndi.binary_dilation(wedge, morphology.disk(p['wedge_margin'])) if p['wedge_margin'] > 0 else wedge
    # campione = pareti sottili (top-hat) con isteresi
    free = ~wedge_d & ~glue_d
    th = gs - morphology.opening(gs, morphology.disk(p['tophat_r']))
    bgpix = th[free & (gs <= t1)]
    sd = float(1.4826 * np.median(np.abs(bgpix - np.median(bgpix)))) if bgpix.size else 0.0
    sd = max(sd, 0.02 * t1, 0.3)
    cand = filters.apply_hysteresis_threshold(th, p['k_low'] * sd, p['k_high'] * sd) & free
    cand = morphology.opening(cand, morphology.disk(CAND_OPEN_R))
    lab = measure.label(cand)
    sample = np.zeros_like(cand)
    if lab.max() > 0:
        areas = np.bincount(lab.ravel())[1:]
        main = lab == (1 + int(np.argmax(areas)))
        sample = main.copy()
        if main.sum() >= p['min_area']:
            main_label = lab[main][0]
            pending = [r.label for r in measure.regionprops(lab) if r.label != main_label and r.area >= p['attach_min_area']]
            changed = True
            while changed and pending:                  # frammenti vicini al campione (anche a catena), non solo quelli a contatto con la colla
                changed = False
                dist_s = ndi.distance_transform_edt(~sample)
                for lb in list(pending):
                    comp = lab == lb
                    if dist_s[comp].min() <= p['attach_dist']:
                        sample |= comp; pending.remove(lb); changed = True
        else:
            sample = np.zeros_like(cand)
    # il campione e' attaccato alla colla: la chiusura si fa insieme a colla e cuneo, cosi' il bordo = contorno della colla
    solid = sample | glue_d | wedge_d
    closed = ndi.binary_fill_holes(morphology.closing(solid, morphology.disk(p['close_r'])))
    roi = closed & ~glue_d & ~wedge_d
    lab = measure.label(roi)
    if lab.max() > 0 and sample.any():
        keep = np.unique(lab[sample & roi]); keep = keep[keep > 0]
        roi = np.isin(lab, keep)
    roi = morphology.opening(roi, morphology.disk(ROI_OPEN_R))
    if p.get('cavity_close_r', 0) > 0 and sample.any():
        # cavita' interne (es. il vuoto di un estruso tubolare chiuso dalle pareti e dalla colla): regioni racchiuse dalla chiusura con
        # raggio piu' grande e adiacenti al campione; il contorno esterno resta quello stretto
        big = morphology.closing(solid, morphology.disk(p['cavity_close_r']))
        holes = ndi.binary_fill_holes(big) & ~big
        hl, hn = ndi.label(holes)
        near_sample = ndi.binary_dilation(sample, morphology.disk(CAVITY_NEAR_R))
        for k in range(1, hn + 1):
            comp = hl == k
            if comp.sum() < p['min_area']:
                continue
            bd = comp & ~ndi.binary_erosion(comp)
            if bd.sum() and (bd & near_sample).sum() >= 0.3 * bd.sum():
                roi = roi | (comp & ~glue_d & ~wedge_d)
        roi = ndi.binary_fill_holes(roi) & ~glue_d & ~wedge_d
    if p.get('outer_margin', 0) > 0:                     # include l'ultimo strato di parete esterno
        roi = ndi.binary_dilation(roi, morphology.disk(p['outer_margin'])) & ~glue_d & ~wedge_d
    return dict(roi=roi, wedge=wedge_d, glue=glue_d & ~wedge_d, t1=float(t1), t2=float(t2), walls=sample)


def work_slice(vol, z, ds):
    return np.asarray(vol[z])[::ds, ::ds]

def roi_volume(vol, p, step, smooth_z, ds):
    """ROI (Z,Y,X) bool alla griglia del volume ridotto, piu' le soglie usate."""
    Z, Y, X = vol.shape
    pr = dict(p)
    r0 = make_roi_slice(work_slice(vol, Z // 2, ds), **pr)
    pr['t1'], pr['t2'] = r0['t1'], r0['t2']             # soglie stimate sulla slice centrale e riusate
    h, w = r0['roi'].shape
    small = np.zeros((Z, h, w), bool)
    keys = list(range(0, Z, step))
    if keys[-1] != Z - 1:
        keys.append(Z - 1)
    t0 = time.time(); announced = False
    def sdf(m):
        return (ndi.distance_transform_edt(m) - ndi.distance_transform_edt(~m)).astype(np.float32)
    prev_z, prev_d = None, None
    for i, z in enumerate(keys):
        t1 = time.time()
        m = make_roi_slice(work_slice(vol, z, ds), **pr)['roi']
        if not announced:
            announced = True
            print(f"   ROI: {time.time()-t1:.1f} s per slice calcolata, {len(keys)} slice -> stima {(time.time()-t1)*len(keys)/60:.1f} min", flush=True)
        d = sdf(m)
        if prev_z is None:
            small[z] = m
        else:                                              # forma interpolata tra due slice calcolate (distanza con segno)
            for zz in range(prev_z + 1, z + 1):
                t = (zz - prev_z) / (z - prev_z)
                small[zz] = ((1 - t) * prev_d + t * d) > 0
        prev_z, prev_d = z, d
        if i % max(len(keys) // 10, 1) == 0:
            print(f"   ROI slice {z}/{Z}  ({time.time()-t0:.0f}s)", flush=True)
    if smooth_z and smooth_z > 1:                        # voto a maggioranza lungo z
        half = smooth_z // 2
        voted = np.zeros_like(small)
        for z in range(Z):
            lo, hi = max(0, z - half), min(Z, z + half + 1)
            voted[z] = small[lo:hi].sum(0, dtype=np.uint16) * 2 > (hi - lo)
        small = voted
    roi = np.zeros((Z, Y, X), bool)
    for z in range(Z):
        roi[z] = upsample_mask(small[z], (Y, X))
    return roi, pr


def roi_axial_envelope(vol, *, max_gap=16, seed_fraction=.75):
    """Experimental axial convex envelope for bright, axially aligned specimens.

    No truth mask used. Assumes convex XY cross sections, brighter material than
    support, separated support in Z. Interpolates internal empty slices only;
    unobserved terminal voids cannot be inferred. Not a general arbitrary-shape ROI.
    Returns mask and diagnostic metadata; raises on ambiguous long axial gaps.
    """
    if not 0.5 < seed_fraction < 1 or max_gap < 0: raise ValueError('invalid ROI parameters')
    vol=np.asarray(vol)
    if vol.ndim!=3 or not np.isfinite(vol).all(): raise ValueError('expected finite ZYX volume')
    # Bounded subsample for intensity statistics, not for segmentation.
    sample=vol[::2,::2,::2]
    lo,hi=map(float,np.percentile(sample,[10,95]))
    if hi<=lo: raise ValueError('no intensity contrast')
    low=lo+.5*(hi-lo); high=lo+seed_fraction*(hi-lo)
    roi=np.zeros(vol.shape,bool); observed=[]
    for z, plane in enumerate(vol):
        if np.count_nonzero(plane>=high)<16: continue
        fg=plane>=low
        # Eliminate small islands before hull; keep all significant material fragments.
        fg=_remove_small_objects_legacy(fg,8)
        if not fg.any(): continue
        roi[z]=morphology.convex_hull_image(fg)
        observed.append(z)
    if not observed: raise ValueError('no bright specimen slices')
    for a,b in zip(observed[:-1],observed[1:]):
        if b-a-1>max_gap: raise ValueError('ambiguous axial gap exceeds max_gap')
        if b-a>1:
            da=ndi.distance_transform_edt(roi[a])-ndi.distance_transform_edt(~roi[a])
            db=ndi.distance_transform_edt(roi[b])-ndi.distance_transform_edt(~roi[b])
            for z in range(a+1,b):
                w=(z-a)/(b-a); roi[z]=(1-w)*da+w*db>0
    return roi,dict(method='axial_convex_envelope',low=low,high=high,first_z=observed[0],last_z=observed[-1],observed_slices=len(observed),interpolated_slices=observed[-1]-observed[0]+1-len(observed),max_gap=max_gap)


def segment_midpoint(img, roi, sigma=.5, min_obj=8):
    """Candidate two-phase threshold: midpoint of raw Otsu-class medians.

    Uses the original normalized smoothing and cleanup with an explicit threshold.
    Assumes two distinguishable intensity populations inside the ROI.
    """
    vals=np.asarray(img)[roi]
    if not vals.size or vals.min()==vals.max(): raise ValueError('two intensity classes required')
    t=filters.threshold_otsu(vals)
    lo=vals[vals<=t]; hi=vals[vals>t]
    if not lo.size or not hi.size: raise ValueError('empty intensity class')
    threshold=.5*(float(np.median(lo))+float(np.median(hi)))
    return segment(img,roi,sigma,threshold,min_obj)


def upsample_mask(m, shape):
    Y, X = shape
    if m.shape == (Y, X):
        return m
    try:
        import cv2
        return cv2.resize(m.astype(np.uint8) * 255, (X, Y), interpolation=cv2.INTER_LINEAR) > 127
    except ImportError:
        ky, kx = math.ceil(Y / m.shape[0]), math.ceil(X / m.shape[1])
        return np.kron(m, np.ones((ky, kx), bool))[:Y, :X]

def overlay(img, res, vmax=None):
    g = np.asarray(img, dtype=np.float32)
    vmax = vmax or (np.percentile(g, 85) * 1.6 + 1)
    rgb = np.dstack([np.clip(g / vmax, 0, 1)] * 3)
    for m, c in ((res['wedge'], (0.2, 0.4, 1.0)), (res['glue'], (1.0, 0.2, 0.2)), (res['roi'], (0.1, 0.9, 0.2))):
        edge = m & ~ndi.binary_erosion(m, iterations=2)
        rgb[edge] = c
    return (rgb * 255).astype(np.uint8)

def slice_overlay(vol, z, p, ds, roi_vol=None, thr=None):
    """Cuneo, colla e ROI di una slice (per anteprima e controllo), sulla griglia di lavoro della ROI."""
    pr = dict(p)
    if thr:
        pr['t1'], pr['t2'] = thr
    img = work_slice(vol, z, ds)
    r = make_roi_slice(img, **pr)
    roi = r['roi'] if roi_vol is None else (np.asarray(roi_vol[z])[::ds, ::ds] > 0)
    return img, dict(wedge=r['wedge'], glue=r['glue'], roi=roi, walls=r['walls']), (r['t1'], r['t2'])

def save_roi_files(stem, roi):
    """ROI alla risoluzione del volume ridotto: npz (1 bit per voxel) e stack TIFF 0/255."""
    nz, ny, nx = roi.shape
    packed = np.stack([np.packbits(roi[z].ravel()) for z in range(nz)])
    np.savez_compressed(stem + '_roi.npz', packed=packed, shape=np.array(roi.shape))
    try:
        import tifffile
        with tifffile.TiffWriter(stem + '_roi.tif', bigtiff=True) as tw:
            for z in range(nz):
                tw.write((roi[z] * 255).astype(np.uint8), compression='zlib', contiguous=False)
    except ImportError:
        pass

# --- Original notebook cell 29 (zero-based) ---
def prepare_working(img_red, roi_red, ds, pad):
    """Volume di analisi (float32) e ROI, eventualmente ridotti ancora di ds, ritagliati sul box della ROI con un margine di pad voxel.
    Si converte in float32 solo la parte ritagliata e si lavora su copie: i volumi interi possono essere liberati."""
    if ds > 1:
        Z, Y, X = img_red.shape; Zc, Yc, Xc = (Z // ds) * ds, (Y // ds) * ds, (X // ds) * ds
        img = img_red[:Zc, :Yc, :Xc].reshape(Zc // ds, ds, Yc // ds, ds, Xc // ds, ds).mean((1, 3, 5), dtype=np.float32)
        roi = roi_red[:Zc, :Yc, :Xc].reshape(Zc // ds, ds, Yc // ds, ds, Xc // ds, ds).mean((1, 3, 5), dtype=np.float32) > 0.5
        full_img = True
    else:
        img = img_red; roi = np.asarray(roi_red, dtype=bool); full_img = False
    zz, yy, xx = np.nonzero(roi.any((1, 2))), np.nonzero(roi.any((0, 2))), np.nonzero(roi.any((0, 1)))
    lo = [int(zz[0][0]), int(yy[0][0]), int(xx[0][0])]; hi = [int(zz[0][-1]) + 1, int(yy[0][-1]) + 1, int(xx[0][-1]) + 1]
    lo = [max(0, v - pad) for v in lo]; hi = [min(s, v + pad) for v, s in zip(hi, roi.shape)]
    sl = tuple(slice(a, b) for a, b in zip(lo, hi))
    img_c = np.array(img[sl], dtype=np.float32, copy=True)
    roi_c = np.array(roi[sl], dtype=bool, copy=True)
    return img_c, roi_c, dict(origin=lo, shape=roi_c.shape)
# ---------------------------------------------------------------- segmentazione
def segment(img, roi, sigma, threshold, min_obj):
    gs = ndi.gaussian_filter(img, sigma) if sigma > 0 else img
    if sigma > 0:                    # lisciatura normalizzata nella ROI: i voxel di bordo non si mescolano con l'aria esterna
        num = ndi.gaussian_filter(np.where(roi, img, 0.0).astype(np.float32), sigma)
        den = ndi.gaussian_filter(roi.astype(np.float32), sigma)
        np.maximum(den, 1e-3, out=den); num /= den; del den
        gs[roi] = num[roi]; del num
    T = float(threshold) if threshold else float(filters.threshold_otsu(gs[roi]))
    material = (gs >= T) & roi
    pores = (gs < T) & roi
    if min_obj > 1:
        material = _remove_small_objects_legacy(material, min_obj)
        pores = roi & ~material
        pores = _remove_small_objects_legacy(pores, min_obj)
        material = roi & ~pores
    exterior = ~roi & (gs < T)                        # aria esterna: fuori ROI e al livello dei pori (cuneo e colla sono piu' chiari)
    return gs, T, material, pores, exterior

def _structure(conn):
    return ndi.generate_binary_structure(3, 1 if conn == 1 else 3)

# ---------------------------------------------------------------- porosita' totale / aperta / chiusa
def porosity_open_closed(pores, exterior, roi, conn):
    st = _structure(conn)
    lab, n = ndi.label(pores, structure=st)
    touch = ndi.binary_dilation(exterior, structure=ndi.generate_binary_structure(3, 1)) & pores
    open_labels = np.unique(lab[touch]); open_labels = open_labels[open_labels > 0]
    lut = np.zeros(n + 1, bool); lut[open_labels] = True
    open_mask = lut[lab]
    closed_mask = pores & ~open_mask
    v = float(roi.sum())
    return dict(porosita_totale=float(pores.sum()) / v, porosita_aperta=float(open_mask.sum()) / v,
                porosita_chiusa=float(closed_mask.sum()) / v, n_pori_connessi=int(n)), lab, lut

# ---------------------------------------------------------------- spessore locale (sfere inscritte)
def local_thickness(mask, vox_um, levels):
    """Spessore locale (diametro in um) di ogni voxel di mask: diametro della sfera piu' grande che lo contiene (Hildebrand-Ruegsegger, approssimato a 'levels' raggi)."""
    dist = _edt32(mask)
    rmax = float(dist.max())
    if rmax < 1.0:
        return np.full(mask.shape, np.nan, np.float32), np.array([])
    radii = np.unique(np.round(np.geomspace(rmax, 1.0, levels), 3))[::-1]
    lt = np.zeros(mask.shape, np.float32)
    seeds = np.empty(mask.shape, bool); cover = np.empty(mask.shape, bool)
    for r in radii:
        np.greater_equal(dist, np.float32(r), out=seeds)
        if not seeds.any():
            continue
        np.logical_not(seeds, out=seeds)
        d2 = _edt32(seeds)
        np.less_equal(d2, np.float32(r), out=cover); del d2
        cover &= mask; cover &= (lt == 0)
        lt[cover] = 2.0 * r * vox_um
    lt[mask & (lt == 0)] = 2.0 * radii[-1] * vox_um
    return lt, radii * 2.0 * vox_um
def thickness_stats(lt, mask, classes_um, edges):
    v = lt[mask]
    v = v[v > 0]
    if v.size == 0:
        return dict(media=np.nan, sd=np.nan, mediana=np.nan, d10=np.nan, d90=np.nan), None, {}
    hist, _ = np.histogram(v, bins=edges)
    frac = hist / hist.sum()
    cum_ge = 1.0 - np.concatenate([[0], np.cumsum(frac)[:-1]])      # frazione del volume con spessore >= bordo inferiore
    st = dict(media=float(v.mean()), sd=float(v.std()), mediana=float(np.median(v)), d10=float(np.percentile(v, 10)), d90=float(np.percentile(v, 90)))
    cls = {}
    if classes_um:
        b = [0] + list(classes_um) + [np.inf]
        for lo, hi in zip(b[:-1], b[1:]):
            lab = f"{int(lo)}-{int(hi)}" if np.isfinite(hi) else f">{int(lo)}"
            cls[lab] = float(((v >= lo) & (v < hi)).mean())
    return st, pd.DataFrame(dict(spessore_um=edges[:-1], frazione_volume=frac, frazione_cumulata_maggiore=cum_ge)), cls

# ---------------------------------------------------------------- pori: separazione e geometria
def fibonacci_dirs(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]

def pore_objects(pores, exterior, lab_cc, lut_open_cc, vox_um, h, min_vox, max_geom, ndirs):
    dist = _edt32(pores)
    dsm = ndi.gaussian_filter(dist, WATERSHED_SIGMA); del dist
    hm = _h_maxima(dsm, h)
    markers, nm = ndi.label(hm); del hm
    np.negative(dsm, out=dsm)
    ws = segmentation.watershed(dsm, markers, mask=pores); del dsm, markers
    n = int(ws.max())
    nz_, plane = ws.shape[0], int(np.prod(ws.shape[1:]))
    ch = max(1, int(8_000_000 // max(plane, 1)))                      # piani per blocco
    vols = np.zeros(n + 1, np.int64)
    first = np.zeros(n + 1, np.int64) - 1
    for z0 in range(0, nz_, ch):
        sub = ws[z0:z0 + ch].ravel()
        vols += np.bincount(sub, minlength=n + 1)
        idx = np.flatnonzero(sub)
        if idx.size:
            uniq, pos = np.unique(sub[idx], return_index=True)
            new = first[uniq] < 0
            first[uniq[new]] = idx[pos[new]] + z0 * plane
    vols = vols[1:]
    cc_of = np.zeros(n + 1, np.int64); ok = first >= 0
    cc_of[ok] = lab_cc.ravel()[first[ok]]
    touch = ndi.binary_dilation(exterior, structure=ndi.generate_binary_structure(3, 1)) & (ws > 0)
    touch_ids = np.unique(ws[touch]); touch_ids = touch_ids[touch_ids > 0]
    touching = np.zeros(n + 1, bool); touching[touch_ids] = True
    rows = []
    order = np.argsort(-vols)
    dirs = fibonacci_dirs(ndirs)
    objs = ndi.find_objects(ws)
    for rank, i in enumerate(order):
        lbl = int(i) + 1
        v = int(vols[i])
        if v < min_vox:
            continue
        rec = dict(id=lbl, volume_um3=v * vox_um ** 3, diametro_equivalente_um=(6 * v / math.pi) ** (1 / 3) * vox_um,
                   connessa_all_esterno=bool(lut_open_cc[cc_of[lbl]]), a_contatto_con_esterno=bool(touching[lbl]))
        if rank < max_geom and objs[i] is not None:
            sub = ws[objs[i]] == lbl
            c = np.argwhere(sub).astype(np.float64)
            if len(c) >= GEOMETRY_MIN_VOXELS:
                cm = c.mean(0); cov = np.cov((c - cm).T)
                w, vec = np.linalg.eigh(cov); w = np.clip(w, 1e-9, None)
                a = np.sqrt(5 * w)                                     # semiassi dell'ellissoide equivalente
                rec['aspetto'] = float(a[2] / a[0])
                axis = vec[:, 2]
                rec['angolo_asse_maggiore_z_gradi'] = float(np.degrees(np.arccos(abs(axis[0]))))   # asse 0 = z
                try:
                    bd = sub & ~ndi.binary_erosion(sub)
                    cb = np.argwhere(bd).astype(np.float64)
                    off = np.array([[a, b, d] for a in (-.5, .5) for b in (-.5, .5) for d in (-.5, .5)])
                    pts = np.unique((cb[:, None, :] + off[None, :, :]).reshape(-1, 3), axis=0)     # angoli dei voxel di bordo
                    hull = ConvexHull(pts)
                    hv = pts[hull.vertices]
                    wid = np.ptp(hv @ dirs.T, axis=0)
                    rec['feret_min_um'] = float(wid.min() * vox_um); rec['feret_medio_um'] = float(wid.mean() * vox_um)
                    if len(hv) <= 4000:
                        from scipy.spatial.distance import pdist
                        rec['feret_max_um'] = float(pdist(hv).max() * vox_um)
                    else:
                        rec['feret_max_um'] = float(np.ptp(hv @ fibonacci_dirs(400).T, axis=0).max() * vox_um)
                    rec['solidita'] = float(min(1.0, len(c) / max(hull.volume, 1.0)))
                except Exception:
                    pass
        rows.append(rec)
    return pd.DataFrame(rows)

# ---------------------------------------------------------------- superficie, Eulero, anisotropia
def surface_stats(material, roi, vox_um, conn, compute_aniso, ndirs):
    """Superficie specifica e anisotropia (MIL). La lisciatura e la triangolazione si fanno a blocchi di piani (margine di 4 piani per la
    lisciatura, un piano in comune per la triangolazione): le aree si sommano e il risultato e' lo stesso di una sola triangolazione, con molta meno memoria."""
    out = {}
    inner = ndi.binary_erosion(roi, iterations=SURFACE_EROSION)
    Z, Y, X = material.shape; HALO = max(4, int(math.ceil(4 * SURFACE_SIGMA)))
    sm = np.empty(material.shape, np.float32)
    ch = max(8, int(4_000_000 // max(Y * X, 1)))
    for z0 in range(0, Z, ch):
        z1 = min(Z, z0 + ch); a, b = max(0, z0 - HALO), min(Z, z1 + HALO)
        sm[z0:z1] = ndi.gaussian_filter(material[a:b].astype(np.float32), SURFACE_SIGMA)[z0 - a:z1 - a]
    SLAB = max(1, int(250_000 // max(Y * X, 1)))                      # celle per blocco: memoria costante qualunque sia il volume
    D = fibonacci_dirs(ndirs) if compute_aniso else None
    S = 0.0; PLs = np.zeros(len(D)) if compute_aniso else None; axs = np.zeros(3)
    axes = [np.array(d, float) for d in ([1, 0, 0], [0, 1, 0], [0, 0, 1])]
    for z0 in range(0, Z - 1, SLAB):
        z1 = min(z0 + SLAB, Z - 1)
        if not inner[z0:z1 + 1].any():
            continue
        try:
            verts, faces, normals, _ = measure.marching_cubes(sm[z0:z1 + 1], level=0.5, mask=inner[z0:z1 + 1])
        except (ValueError, RuntimeError):
            continue                                                  # nessuna superficie in questo blocco
        tri = verts[faces]
        cr = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        area = 0.5 * np.linalg.norm(cr, axis=1)
        nrm = cr / (2 * np.maximum(area, 1e-12))[:, None]
        S += float(area.sum())
        if compute_aniso:
            for s in range(0, len(area), 500000):
                PLs += (area[s:s + 500000, None] * np.abs(nrm[s:s + 500000] @ D.T)).sum(0)
            for k, d in enumerate(axes):
                axs[k] += float((area * np.abs(nrm @ d)).sum())
        del verts, faces, normals, tri, cr, area, nrm
    del sm
    S = S * vox_um ** 2                                              # um^2
    ninner = float(inner.sum())
    Vroi = ninner * vox_um ** 3
    Vmat = float((material & inner).sum()) * vox_um ** 3
    out['superficie_specifica_per_volume_roi_1_per_mm'] = S / Vroi * 1000.0
    out['superficie_su_volume_materiale_1_per_mm'] = S / max(Vmat, 1.0) * 1000.0
    if compute_aniso:
        PL = PLs / ninner                                            # intersezioni per unita' di lunghezza (in voxel^-1)
        mil = vox_um / PL                                            # lunghezza media di intercetta (um)
        A = np.c_[D[:, 0] ** 2, D[:, 1] ** 2, D[:, 2] ** 2, 2 * D[:, 0] * D[:, 1], 2 * D[:, 0] * D[:, 2], 2 * D[:, 1] * D[:, 2]]
        m = np.linalg.lstsq(A, 1.0 / mil ** 2, rcond=None)[0]
        M = np.array([[m[0], m[3], m[4]], [m[3], m[1], m[5]], [m[4], m[5], m[2]]])
        w, vec = np.linalg.eigh(M); w = np.clip(w, 1e-12, None)
        ax = 1.0 / np.sqrt(w)                                        # semiassi dell'ellissoide di MIL
        for name, k in (('z', 0), ('y', 1), ('x', 2)):
            out[f'MIL_{name}_um'] = float(vox_um / (axs[k] / ninner))
        out['DA_MIL_max_su_min'] = float(ax.max() / ax.min())
        out['DA_1_meno_min_su_max'] = float(1 - ax.min() / ax.max())
        out['asse_principale_angolo_z_gradi'] = float(np.degrees(np.arccos(abs(vec[0, np.argmin(w)]))))
        out['MIL_max_um'] = float(ax.max()); out['MIL_min_um'] = float(ax.min())
    return out
def euler_stats(material, roi, vox_um, conn):
    chi = int(measure.euler_number(material & roi, connectivity=conn if conn == 1 else 3))
    v_mm3 = float(roi.sum()) * (vox_um / 1000.0) ** 3
    return dict(numero_di_euler=chi, densita_connettivita_per_mm3=(1 - chi) / v_mm3)

# ---------------------------------------------------------------- analisi 2D sui piani
def feret_min_2d(coords, nang=36):
    ang = np.linspace(0, np.pi, nang, endpoint=False)
    d = np.c_[np.cos(ang), np.sin(ang)]
    try:
        hv = coords[ConvexHull(coords).vertices]
    except Exception:
        hv = coords
    return float((np.ptp(hv @ d.T, axis=0) + 1.0).min())

def mil_axes_2d(material, roi):
    """Intercette lungo le due direzioni del piano: pixel della ROI in linee / numero di transizioni."""
    res = []
    for ax in (0, 1):
        m = material if ax == 0 else material.T
        r = roi if ax == 0 else roi.T
        both = r[1:] & r[:-1]
        trans = int(((m[1:] != m[:-1]) & both).sum())
        length = int(r.sum())
        res.append(length / trans if trans else np.nan)
    return res                                                      # [lungo asse 0, lungo asse 1] (in pixel)

def analyze_plane(mat2, por2, roi2, vox_um):
    st = dict(porosita_2D=float(por2.sum()) / max(float(roi2.sum()), 1.0))
    lab = measure.label(por2, connectivity=1)
    props = measure.regionprops(lab)
    ed, fmax, fmin, asp = [], [], [], []
    for p in props:
        if p.area < MIN_PORE_PIXELS_2D:
            continue
        if EXCLUDE_EDGE_PORES_2D:
            r0, c0, r1, c1 = p.bbox
            if r0 == 0 or c0 == 0 or r1 == lab.shape[0] or c1 == lab.shape[1]:
                continue
        ed.append(getattr(p, 'equivalent_diameter_area', None) if hasattr(p, 'equivalent_diameter_area') else p.equivalent_diameter)
        ed[-1] = ed[-1] * vox_um
        try:
            fmax.append(p.feret_diameter_max * vox_um)
        except Exception:
            fmax.append(np.nan)
        fmin.append(feret_min_2d(p.coords.astype(float)) * vox_um)
        asp.append((getattr(p, 'axis_major_length', None) or p.major_axis_length) / max((getattr(p, 'axis_minor_length', None) or p.minor_axis_length), 1.0))
    area_um2 = float(roi2.sum()) * vox_um ** 2
    st.update(n_pori_2D=len(ed), pori_per_mm2=len(ed) / (area_um2 / 1e6) if area_um2 else np.nan,
              diametro_equivalente_medio_um=float(np.mean(ed)) if ed else np.nan,
              diametro_equivalente_mediano_um=float(np.median(ed)) if ed else np.nan,
              feret_max_medio_um=float(np.nanmean(fmax)) if ed else np.nan, feret_min_medio_um=float(np.mean(fmin)) if ed else np.nan,
              aspetto_mediano=float(np.median(asp)) if ed else np.nan)
    if mat2.any():
        skel, dist = _medial_axis(mat2)
        t = 2.0 * dist[skel] * vox_um
        st.update(spessore_parete_medio_um=float(t.mean()), spessore_parete_mediano_um=float(np.median(t)))
    else:
        st.update(spessore_parete_medio_um=np.nan, spessore_parete_mediano_um=np.nan)
    mi = mil_axes_2d(mat2, roi2)
    st['MIL_asse0_um'], st['MIL_asse1_um'] = [v * vox_um for v in mi]
    return st

def run_2d(material, pores, roi, vox_um, ds, planes, step_orig, origin=(0, 0, 0)):
    step = max(1, int(round(step_orig / ds)))
    rows = []
    names = {'z': ('z', 'y', 'x'), 'y': ('y', 'z', 'x'), 'x': ('x', 'z', 'y')}      # asse piano -> (asse indice, asse0 del piano, asse1 del piano)
    for pl in planes:
        n = {'z': material.shape[0], 'y': material.shape[1], 'x': material.shape[2]}[pl]
        for i in range(0, n, step):
            if pl == 'z': m, p, r = material[i], pores[i], roi[i]
            elif pl == 'y': m, p, r = material[:, i, :], pores[:, i, :], roi[:, i, :]
            else: m, p, r = material[:, :, i], pores[:, :, i], roi[:, :, i]
            if r.sum() < MIN_ROI_PIXELS_2D:
                continue
            st = analyze_plane(m, p, r, vox_um)
            st.update(piano=pl, indice_lavoro=i, posizione_originale=i * ds, posizione_mm=(origin[{'z': 0, 'y': 1, 'x': 2}[pl]] + i) * vox_um / 1000.0, area_roi_mm2=float(r.sum()) * (vox_um / 1000.0) ** 2)
            ax0, ax1 = names[pl][1], names[pl][2]
            st['asse0'], st['asse1'] = ax0, ax1
            rows.append(st)
    return pd.DataFrame(rows)

def mil_by_axis(df2d):
    """Riporta il MIL 2D agli assi z, y, x mediando i piani in cui l'asse compare."""
    acc = {'z': [], 'y': [], 'x': []}
    for _, r in df2d.iterrows():
        for col, ax in (('MIL_asse0_um', r['asse0']), ('MIL_asse1_um', r['asse1'])):
            if np.isfinite(r[col]):
                acc[ax].append(r[col])
    out = {f'MIL2D_{k}_um': (float(np.mean(v)) if v else np.nan) for k, v in acc.items()}
    vals = [v for v in out.values() if np.isfinite(v)]
    out['DA_2D_max_su_min'] = float(max(vals) / min(vals)) if len(vals) >= 2 else np.nan
    return out

# ---------------------------------------------------------------- esempi visivi su alcune slice
def _example_slices(roi, n):
    """Indici (nel volume di lavoro) di n slice equidistanti tra quelle che contengono la ROI."""
    z_with = np.nonzero(roi.reshape(roi.shape[0], -1).any(1))[0]
    if len(z_with) == 0:
        return []
    return sorted(set(int(z_with[int(round(v))]) for v in np.linspace(0, len(z_with) - 1, max(1, n) + 2)[1:-1]))

def segmentation_examples(stem, gs, roi, material, pores, open_mask, vox, T, info, ds):
    """Figura di controllo della segmentazione: per alcune slice, immagine con contorno della ROI e classificazione
    materiale / pori chiusi / pori aperti."""
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    zs = _example_slices(roi, N_EXAMPLE_SLICES)
    if not zs:
        return
    closed = pores & ~open_mask
    fig, ax = plt.subplots(len(zs), 2, figsize=(11, 5.2 * len(zs)))
    ax = np.atleast_2d(ax)
    lo, hi = np.percentile(gs[roi], [1, 99.5])
    for r, z in enumerate(zs):
        g = np.clip((gs[z] - lo) / max(hi - lo, 1e-6), 0, 1)
        ax[r, 0].imshow(g, cmap='gray'); ax[r, 0].contour(roi[z], [0.5], colors='lime', linewidths=0.8)
        v = float(roi[z].sum())
        ax[r, 0].set_title(f"slice originale z = {info['origin'][0] * ds + z * ds}  (soglia di grigio = {T:.0f})", fontsize=9)
        cls = np.zeros(g.shape + (3,), np.float32) + 0.12
        cls[material[z]] = (0.85, 0.85, 0.85)
        cls[closed[z]] = (0.2, 0.45, 1.0)
        cls[open_mask[z]] = (1.0, 0.35, 0.2)
        ax[r, 1].imshow(cls); ax[r, 1].contour(roi[z], [0.5], colors='white', linewidths=0.6)
        if v > 0:
            ax[r, 1].set_title(f"porosita' in questa slice: totale {pores[z].sum()/v:.2f} | aperta {open_mask[z].sum()/v:.2f} | chiusa {closed[z].sum()/v:.2f}", fontsize=9)
        for a in ax[r]: a.axis('off')
    fig.legend(handles=[Patch(color=(0.85, 0.85, 0.85), label='materiale'), Patch(color=(0.2, 0.45, 1.0), label='pori chiusi'),
                        Patch(color=(1.0, 0.35, 0.2), label='pori aperti (connessi all\'aria esterna)'), Patch(color=(0.12, 0.12, 0.12), label='fuori dalla ROI')],
               loc='lower center', ncol=4, fontsize=9)
    plt.tight_layout(rect=(0, 0.03, 1, 1)); plt.savefig(stem + '_segmentazione.png', dpi=110); plt.close(fig)

def thickness_examples(stem, roi, lt_store, material, pores, vox, summary, info, ds):
    """Figura con le mappe dello spessore locale (pareti e pori) su alcune slice, con il valore medio della slice e del volume."""
    import matplotlib
    import matplotlib.pyplot as plt
    zs = _example_slices(roi, N_EXAMPLE_SLICES)
    names = [n for n in ('parete', 'poro') if n in lt_store]
    if not zs or not names:
        return
    masks = dict(parete=material, poro=pores)
    labels = dict(parete='spessore locale della parete (um)', poro='diametro locale dei pori (um)')
    fig, ax = plt.subplots(len(zs), len(names), figsize=(6.2 * len(names), 5.2 * len(zs)))
    ax = np.atleast_2d(ax).reshape(len(zs), len(names))
    vmax = {n: float(np.nanpercentile(lt_store[n][masks[n]].astype(np.float32), 99)) for n in names}     # float16 -> float32: i percentili in float16 vanno in overflow
    for r, z in enumerate(zs):
        for c, n in enumerate(names):
            m = masks[n][z]
            img = np.where(m, lt_store[n][z].astype(np.float32), np.nan)
            ax[r, c].imshow(np.where(roi[z], 0.85, np.nan), cmap='gray', vmin=0, vmax=1)    # grigio chiaro = resto della ROI
            im = ax[r, c].imshow(img, cmap='turbo', vmin=0, vmax=vmax[n])
            plt.colorbar(im, ax=ax[r, c], fraction=0.046, pad=0.02, label=labels[n])
            vals = lt_store[n][z][m].astype(np.float32)
            ms = f"{vals.mean():.0f}" if vals.size else "-"
            mv = summary.get(f'{n}_spessore_media_um', float('nan'))
            ax[r, c].set_title(f"{n}: media nella slice {ms} um | media nel volume {mv:.0f} um   (z = {info['origin'][0] * ds + z * ds})", fontsize=9)
            ax[r, c].axis('off')
    plt.tight_layout(); plt.savefig(stem + '_spessori.png', dpi=110); plt.close(fig)

def analyze_volume(img_red, roi_red, stem, pitch_um, ds):
    vox = pitch_um * ds
    t0 = time.time()
    img, roi, info = prepare_working(img_red, roi_red, ds, PAD_VOXELS)
    print(f"  volume di lavoro {img.shape} (voxel {vox:.1f} um), ROI {int(roi.sum())} voxel; preparazione {time.time()-t0:.0f}s")
    gs, T, material, pores, exterior = segment(img, roi, SEG_SIGMA, THRESHOLD, MIN_OBJECT_VOXELS)
    del img
    summary = dict(file=os.path.basename(stem), voxel_lavoro_um=vox, soglia_grigio=T,
                   volume_roi_mm3=float(roi.sum()) * (vox / 1000.0) ** 3, volume_materiale_mm3=float(material.sum()) * (vox / 1000.0) ** 3)
    dist_tables = {}
    if RUN_3D:
        por, lab_cc, lut_open = porosity_open_closed(pores, exterior, roi, CONNECTIVITY)
        summary.update(por)
        open_mask = lut_open[lab_cc]
        if SAVE_EXAMPLES:
            try:
                segmentation_examples(stem, gs, roi, material, pores, open_mask, vox, T, info, ds)
            except Exception as e:
                print('  esempi di segmentazione non creati:', e)
        del open_mask, gs; gc.collect()
        print(f"  porosita': totale {por['porosita_totale']:.3f} | aperta {por['porosita_aperta']:.3f} | chiusa {por['porosita_chiusa']:.3f}")
        if COMPUTE_THICKNESS:
            wcls = [float(v) for v in WALL_CLASSES_UM.split(',') if v.strip()]
            pcls = [float(v) for v in PORE_CLASSES_UM.split(',') if v.strip()]
            lt_store = {}
            for name, mask, cls in (('parete', material, wcls), ('poro', pores, pcls)):
                t1 = time.time()
                lt, levels_um = local_thickness(mask, vox, PSD_LEVELS)
                edges = np.concatenate([[0], np.sort(levels_um)])
                edges = np.unique(np.concatenate([edges, [lt.max() + 1e-6]]))
                st, tbl, classes = thickness_stats(lt, mask, cls, edges)
                for k, v in st.items(): summary[f'{name}_spessore_{k}_um'] = v
                for k, v in classes.items(): summary[f'{name}_classe_{k}_um'] = v
                if tbl is not None: dist_tables[name] = tbl
                print(f"  spessore locale {name}: media {st['media']:.1f} um, mediana {st['mediana']:.1f} um ({time.time()-t1:.0f}s)")
                frac4 = float((lt[mask] < 4 * vox).mean()) if mask.any() else float('nan')
                summary[f'{name}_frazione_sotto_4_voxel'] = frac4
                if np.isfinite(frac4) and frac4 > 0.2:
                    print(f"  ATTENZIONE: il {frac4*100:.0f}% del volume ({name}) ha spessore sotto 4 voxel ({4 * vox:.0f} um; voxel di lavoro {vox:.1f} um): risoluzione al limite, riduci il passo di campionamento")
                if np.isfinite(st['mediana']) and st['mediana'] < 4 * vox:
                    print(f"  ATTENZIONE: lo spessore mediano ({name}) e' meno di 4 voxel di lavoro ({vox:.1f} um): la risoluzione e' al limite, riduci ANALYSIS_DS")
                if SAVE_EXAMPLES:
                    lt_store[name] = lt.astype(np.float16)           # solo per le figure di controllo
                del lt; gc.collect()
            if SAVE_EXAMPLES:
                try:
                    thickness_examples(stem, roi, lt_store, material, pores, vox, summary, info, ds)
                except Exception as e:
                    print('  esempi di spessore non creati:', e)
            del lt_store
        if COMPUTE_PORE_OBJECTS:
            t1 = time.time()
            df = pore_objects(pores, exterior, lab_cc, lut_open, vox, WATERSHED_H, MIN_PORE_VOXELS, MAX_PORES_GEOMETRY, FERET_DIRECTIONS)
            df.to_csv(stem + '_pori.csv', index=False)
            summary['n_pori_separati'] = int(len(df))
            if len(df):
                summary['pori_diametro_equivalente_medio_um'] = float(df.diametro_equivalente_um.mean())
                summary['pori_diametro_equivalente_mediano_um'] = float(df.diametro_equivalente_um.median())
                summary['pori_volume_peso_diametro_medio_um'] = float(np.average(df.diametro_equivalente_um, weights=df.volume_um3))
                for c in ('aspetto', 'feret_min_um', 'feret_medio_um', 'feret_max_um', 'solidita'):
                    if c in df: summary[f'pori_{c}_medio'] = float(df[c].mean())
                summary['frazione_pori_connessi_all_esterno'] = float((df.volume_um3 * df.connessa_all_esterno).sum() / df.volume_um3.sum())
            print(f"  pori separati: {len(df)} ({time.time()-t1:.0f}s)")
        try:
            summary.update(euler_stats(material, roi, vox, CONNECTIVITY))
        except Exception as e:
            print("  numero di Eulero non calcolato:", e)
        try:
            t1 = time.time()
            summary.update(surface_stats(material, roi, vox, CONNECTIVITY, COMPUTE_ANISOTROPY, N_DIRECTIONS))
            print(f"  superficie / anisotropia ({time.time()-t1:.0f}s)")
        except Exception as e:
            print("  superficie/anisotropia non calcolate:", e)
    df2d = None
    if RUN_2D:
        t1 = time.time()
        planes = [p.strip() for p in PLANES.split(',') if p.strip()]
        df2d = run_2d(material, pores, roi, vox, ds, planes, STEP_2D, info['origin'])
        df2d.to_csv(stem + '_2D.csv', index=False)
        for pl in planes:
            d = df2d[df2d.piano == pl]
            if len(d):
                summary[f'2D_{pl}_n_slice'] = int(len(d))
                for c in ('porosita_2D', 'diametro_equivalente_medio_um', 'feret_max_medio_um', 'aspetto_mediano', 'spessore_parete_medio_um', 'pori_per_mm2'):
                    summary[f'2D_{pl}_{c}'] = float(d[c].mean())
        summary.update(mil_by_axis(df2d))
        print(f"  analisi 2D: {len(df2d)} slice ({time.time()-t1:.0f}s)")
    if dist_tables:
        merged = None
        for name, tbl in dist_tables.items():
            tb = tbl.rename(columns={'frazione_volume': f'{name}_frazione_volume', 'frazione_cumulata_maggiore': f'{name}_frazione_cumulata_maggiore', 'spessore_um': f'{name}_spessore_um'})
            merged = tb if merged is None else pd.concat([merged, tb], axis=1)
        merged.to_csv(stem + '_distribuzioni.csv', index=False)
    return summary, dist_tables, df2d

def make_figures(stem, summary, dist_tables, df2d):
    import matplotlib
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(17, 4.6))
    for name, col in (('poro', '#d62728'), ('parete', '#2878d6')):
        if name in dist_tables:
            t = dist_tables[name]
            ax[0].plot(t.spessore_um, t.frazione_cumulata_maggiore, color=col, label='pori (distribuzione porosimetrica)' if name == 'poro' else 'pareti')
            ax[1].plot(t.spessore_um, t.frazione_volume, color=col, label=name)
    ax[0].set_xlabel('diametro / spessore locale (um)'); ax[0].set_ylabel('frazione di volume >= x'); ax[0].set_title('distribuzione cumulata'); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].set_xlabel('diametro / spessore locale (um)'); ax[1].set_ylabel('frazione di volume'); ax[1].set_title('distribuzione'); ax[1].legend(); ax[1].grid(alpha=.3)
    if df2d is not None and len(df2d):
        for pl, col in (('z', '#2a9d4a'), ('y', '#e8a200'), ('x', '#6a3fb5')):
            d = df2d[df2d.piano == pl]
            if len(d): ax[2].plot(d.posizione_originale, d.porosita_2D, '.-', color=col, label=f'piano normale a {pl}')
        ax[2].set_xlabel('posizione lungo l\'asse del piano (slice originali)'); ax[2].set_ylabel('porosita\' 2D'); ax[2].set_title('porosita\' per slice (ogni STEP_2D)'); ax[2].legend(); ax[2].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(stem + '_grafici.png', dpi=110); plt.close(fig)

def synthetic_vox(path, n=(96,176,176), pitch=35.6, seed=0):
    rng = np.random.default_rng(seed); nz,ny,nx = n
    z,y,x = np.mgrid[0:nz,0:ny,0:nx].astype(np.float32)
    vol = rng.normal(300,40,n).astype(np.float32)                                    # aria + rumore
    env = (((z-nz/2)/(nz*0.42))**2 + ((y-ny*0.52)/(ny*0.36))**2 + ((x-nx*0.5)/(nx*0.40))**2) < 1
    # schiuma: pareti = complemento di bolle sferiche (Poisson); materiale ~ 18000
    pores = np.zeros(n,bool)
    for _ in range(70):
        c = np.array([rng.uniform(.18,.82)*nz, rng.uniform(.2,.8)*ny, rng.uniform(.15,.85)*nx]); r = rng.uniform(7,13)
        pores |= ((z-c[0])**2+(y-c[1])**2+(x-c[2])**2) < r*r
    foam = env & ~pores
    vol[foam] = rng.normal(18000,900,foam.sum())
    vol[(y>ny*0.90)&(x>nx*0.30)&(x<nx*0.55)] = rng.normal(60000,1500)               # colla
    vol[(y<ny*0.12)&(x>nx*0.55)] = rng.normal(9000,300)                              # cuneo
    write_vox(path, np.clip(vol,0,65535).astype(np.uint16), pitch); return float(foam.sum()/env.sum()), env

