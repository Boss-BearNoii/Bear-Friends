r"""
cut_audio.py - ตัดเสียงพากย์ดิบอัตโนมัติ เลียนแบบวิธีตัดของคนตัด (เรียนรู้จาก คซ323-324-คซ325-326)

Logic ที่แกะได้จากไฟล์ที่คนตัด:
  1. ตัด "เทคที่อ่านผิด" ทิ้ง: ผู้พากย์อ่านสะดุด/ผิด แล้วย้อนอ่านใหม่ -> เก็บเทคสุดท้าย ตัดเทคก่อนหน้า+ช่วงเงียบ
  2. ตัดคำที่พูดค้างไม่จบ (เช่น "จง..." ก่อนพูด "จนไม่มี...") และเสียงอุทาน/หลุด (โอ้โห, อื้อ, โอเค ...)
  3. ตัดเสียงหายใจ: ช่วงไม่ได้พูด (ตาม VAD) ยาวเกิน 0.9 วิ เหลือ 0.25 วิหลังคำ + 0.2 วิก่อนคำถัดไป
  4. เร่งความเร็วทั้งไฟล์ 1.07x แบบคงระดับเสียง (atempo) และลดเสียง 1.2 dB

ขั้นตอน: แบ่งวรรคจากช่วงเงียบ -> Whisper large-v3 ถอดทีละวรรค (พร้อมเวลารายคำ) -> เทียบข้อความหาเทคซ้ำ
         -> EDL สำหรับ VEGAS + FFmpeg ตัด/รวม

แนะนำ: นำ <output>.vegas.txt เข้า VEGAS (File > Import > EDL Text File) แล้วไล่ฟังเช็คตามเวลาใน <output>.cuts.txt
        ตัวจับเทคผิดได้ราว 80% ของที่คนตัด ยังต้องฟังเก็บงานเอง

ใช้งาน:
  python cut_audio.py "ไฟล์ดิบ.mp3"                     -> ได้ "ไฟล์ดิบ (ตัดเสียงแล้ว).mp4"
  python cut_audio.py "ไฟล์ดิบ.mp3" -o output.mp4
  python cut_audio.py "D:\Bear Friends\คซ"              -> ทุกไฟล์เสียงในโฟลเดอร์ (ข้ามไฟล์ที่มีคำว่า "(ตัดเสียงแล้ว)")
  python cut_audio.py "D:\Bear Friends\คซ\*.mp3" --skip-done --out-dir "D:\ผลลัพธ์"
  python cut_audio.py a.mp3 b.mp3 c.mp3
  python cut_audio.py "ไฟล์ดิบ.mp3" --tempo 1.0 --gain 0  (ไม่เร่ง ไม่ปรับเสียง; ปกติปรับให้ได้ -20.2 LUFS อัตโนมัติ)
  python cut_audio.py "ไฟล์ดิบ.mp3" --no-render  (เอาแค่ EDL + รายการจุดตัด เร็วกว่า)
  python cut_audio.py "ไฟล์ดิบ.mp3" "บท ตอน 323.txt" "บท ตอน 324.txt"  (มีบท -> จับการย้อนอ่านจากบทเพิ่ม)
ไฟล์ข้างเคียง: <output>.vegas.txt (EDL สำหรับ VEGAS: แทร็ก 1 เสียงหลัก, แทร็ก 2 ตัดแล้วแต่ไม่มั่นใจ, แทร็ก 3 น่าสงสัยยังไม่ตัด),
              <output>.review.txt (จุดที่ควรฟังเช็ค), <output>.cuts.txt (รายการจุดที่ตัด + เวลาบน timeline),
              <output>.transcript.json (แคชผลถอดเสียง รันซ้ำไม่ต้องถอดใหม่)
"""
import argparse, difflib, glob, json, os, re, site, subprocess, sys, time
import numpy as np

SR = 16000
HOP = 0.02  # 20 ms frames

# ---------------------------------------------------------------- audio
def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def speech_mask(x):
    h = int(SR * HOP); n = len(x) // h
    e = np.log(np.square(x[:n * h].reshape(n, h)).mean(1) + 1e-9)
    p10, p50 = np.percentile(e, [10, 50])
    return e > p10 + 0.4 * (p50 - p10), e

def utterances(sp, min_sil=0.2, max_len=28.0):
    d = np.diff(np.concatenate([[0], sp.astype(int), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    U = []
    for a, b in zip(st, en):
        if U and (a - U[-1][1]) * HOP < min_sil and (b - U[-1][0]) * HOP < max_len:
            U[-1][1] = b
        else:
            U.append([a, b])
    return [(max(0.0, a * HOP - 0.05), b * HOP + 0.05) for a, b in U if (b - a) * HOP >= 0.1]

# ---------------------------------------------------------------- whisper
_PIPE = {}

def get_pipe(model_name):
    """โหลด Whisper ครั้งเดียว ใช้ซ้ำทุกไฟล์"""
    if model_name not in _PIPE:
        for d in glob.glob(os.path.join(site.getsitepackages()[-1], "nvidia", "*", "bin")):  # CUDA DLLs from pip
            os.add_dll_directory(d); os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
        from faster_whisper import WhisperModel, BatchedInferencePipeline
        try:
            model = WhisperModel(model_name, device="cuda", compute_type="float16")
        except Exception as ex:
            print("  GPU ใช้ไม่ได้ -> ใช้ CPU (ช้ากว่ามาก):", ex)
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
        _PIPE[model_name] = BatchedInferencePipeline(model)
    return _PIPE[model_name]

def _run_part(pipe, x, part, bs):
    while True:
        try:
            segs, _ = pipe.transcribe(x, language="th", word_timestamps=True, batch_size=bs, beam_size=1,
                                      clip_timestamps=[{"start": a, "end": b} for a, b in part])
            return list(segs)
        except RuntimeError as ex:
            if "out of memory" not in str(ex).lower() or bs == 1:
                raise
            bs = max(1, bs // 2)
            print(f"\n  GPU หน่วยความจำไม่พอ ลด batch เหลือ {bs}")

def transcribe(x, U, model_name):
    """ถอดทีละวรรค (ได้คำที่อ่านผิดครบกว่าถอดรวด) พร้อมเวลาของแต่ละคำ"""
    pipe = get_pipe(model_name)
    res, t0, B = [], time.time(), 64
    for k in range(0, len(U), B):
        part = U[k:k + B]
        segs = _run_part(pipe, x, part, 16)
        rows = [{"start": a, "end": b, "text": "", "words": []} for a, b in part]
        for s in segs:
            # segment -> clip that contains its start
            i = min(range(len(part)), key=lambda q: 0 if part[q][0] - 0.3 <= s.start <= part[q][1] else
                    min(abs(s.start - part[q][0]), abs(s.start - part[q][1])))
            rows[i]["text"] = (rows[i]["text"] + " " + s.text.strip()).strip()
            rows[i]["words"] += [[round(float(w.start), 3), round(float(w.end), 3), w.word] for w in (s.words or [])]
        res += rows
        done = min(len(U), k + B)
        el = time.time() - t0
        print(f"\r  ถอดเสียง {100 * done / len(U):5.1f}%  ({done}/{len(U)} วรรค, {el:.0f}s, เหลือ ~{el / done * (len(U) - done):.0f}s)", end="", flush=True)
    print()
    return res

# ---------------------------------------------------------------- retake detection
FILLERS = {"โอ้โห", "โอ้", "โอ้ว", "อื้อ", "อื้อหื้อ", "อือ", "อืม", "อืมม", "เอ่อ", "เออ", "อ่า", "อ้า", "โอเค",
           "หืม", "ฮึ", "เฮ้อ", "อ่ะ", "เอ้า", "อุ๊ย", "ว้าย", "แหะ",
           "อ้าว", "ฮ่าว", "โค้ว", "เฮ้ย", "ฮ่าๆ", "ฮ่าฮ่า"}  # คำอุทานที่คนตัดทิ้งทุกครั้ง (จากไฟล์ คซ317)
# ข้อความที่ Whisper มักเดาขึ้นมาเองจากเสียงรบกวน
HALLU = ("สวัสดีครับ", "สวัสดีค่ะ", "ขอบคุณครับ", "ขอบคุณค่ะ", "ขอบคุณที่รับชม", "ซับไตเติ้ล", "ติดตามช่อง",
         "โปรดติดตาม", "ติดตามตอนต่อไป", "กดไลค์", "กดติดตาม", "แล้วพบกันใหม่")
_VOWELISH = re.compile(r"[อเโแฮหึืุ่้๊๋็ัิีะาำ]+")

def norm(t):
    return re.sub(r"[\s\.,!?\"'…\-]+", "", t)

# พยัญชนะที่ออกเสียงเหมือนกัน -> ตัวเดียวกัน (Whisper มักสะกดชื่อ/คำเดียวกันต่างกันในแต่ละเทค เช่น ฮารี่/หารลี่)
_CANON = str.maketrans("ฮรศษธฑฒภฆฌฎฏณญฬฐถขฃฅผฝฉซ้๊๋",
                       "หลสสทททพคชดตนยลททคคคพฟชส่่่")  # + วรรณยุกต์ทุกตัวถือเป็นตัวเดียว (Whisper สะกด ท่าที/ถ้าที่ สลับกัน)

def canon(t):
    return norm(t).translate(_CANON)

def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()

def _filler_tok(n):
    return n in FILLERS or (len(n) <= 6 and _VOWELISH.fullmatch(n) is not None)

def is_filler(t, dur=None):
    n = norm(t)
    if n == "" or n.isdigit() or _filler_tok(n):
        return True
    toks = [norm(w) for w in re.split(r"[\s,]+", t) if norm(w)]
    if toks and all(_filler_tok(w) for w in toks):  # "โอ้ โอ้ โอ้"
        return True
    rest = n
    for h in sorted(HALLU + ("โปรดติดตามตอนต่อไป",), key=len, reverse=True):
        rest = rest.replace(h, "")
    if len(rest) == len(n):
        return False
    # ผู้พากย์พูด "สวัสดีครับ"/"โปรดติดตามตอนต่อไป" จริงตอนปิดท้าย: ถ้าช่วงเสียงยาวพอจะพูดประโยคนั้นได้ = ของจริง
    # ข้อความเดาเองของ Whisper มักเกิดบนเสียงรบกวนสั้นๆ (เช่น 0.26 วิ)
    if dur is not None and dur >= 0.06 * (len(n) - len(rest)):
        return False
    for f in sorted(FILLERS, key=len, reverse=True):
        rest = rest.replace(f, "")
    return len(rest) <= 4  # เกือบทั้งวรรคเป็นข้อความเดาเอง/เสียงอุทาน

# คำที่ประโยคจบตรงนั้นไม่ได้ ถ้าพูดค้างไว้แล้วพูดใหม่ ("เห็นว่าฮานลี่ไม่ / ไม่ถามอะไรต่อ") ให้ตัดตัวแรกได้
_DANGLING = {canon(w) for w in ("ไม่", "ที่", "และ", "ของ", "ใน", "กับ", "จะ", "ก็", "ว่า", "แต่", "เพื่อ", "ให้", "จาก",
                                "ถึง", "ซึ่ง", "หรือ", "ทั้ง", "ยัง", "เป็น", "คือ", "แล้ว", "เมื่อ", "หาก", "ถ้า", "โดย", "จึง")}

def detect(U, L=10, window=20.0, back=3, thresh=0.6, abandon=0.6, passes=3, frag=3, frag2=6, frag_sim=0.4, min_tail=6, pad=0, mid_thresh=0.8):
    """U: [{start,end,text}] -> [(t0, t1, reason, text)] regions to remove."""
    cuts, items = [], []
    for i, u in enumerate(U):
        # เลขตอนที่ Whisper แยกเป็นวรรคเดี่ยว ("ตอนที่" / "320") เป็นเสียงจริง ห้ามตัด
        is_ep_no = norm(u["text"]).isdigit() and i > 0 and norm(U[i - 1]["text"]).endswith("ตอนที่")
        if not is_ep_no and is_filler(u["text"], u["end"] - u["start"]):
            cuts.append((u["start"], u["end"], "filler", u["text"]))
        else:
            t = canon(u["text"])
            ct = [w[0] for w in (u.get("words") or []) for _ in canon(w[2])]  # เวลาเริ่มของแต่ละตัวอักษร
            items.append(dict(u, t=t, o=norm(u["text"]), ct=ct if len(ct) == len(t) else None))
    for _ in range(passes):
        new, keep = [], [True] * len(items)
        j = 1
        while j < len(items):
            S, prev = items[j]["t"], items[j - 1]
            pt = prev["t"]
            # คำพูดค้าง: วรรคสั้นมาก/ลากเสียงหาย แล้วเริ่มใหม่ด้วยเสียงคล้ายกัน
            if keep[j - 1] and items[j]["start"] - prev["end"] < 3 and (
                    ((len(pt) <= frag or prev["text"].strip().endswith("...")) and S[:1] == pt[:1])
                    or (len(pt) <= frag2 and ratio(pt, S[:len(pt) + 1]) >= frag_sim)):
                new.append((prev["start"], items[j]["start"], "fragment", prev["text"])); keep[j - 1] = False
                j += 1; continue
            if len(S) < 4:
                j += 1; continue
            # อ่านซ้ำ: ต้นวรรคนี้ตรงกับข้อความก่อนหน้าไม่เกิน `back` วรรค และข้อความที่ถูกทิ้งทั้งท่อนคล้ายต้นเทคใหม่
            # เทคใหม่อาจถูกแบ่งเป็นหลายวรรค -> เอาวรรคถัดๆ ไปต่อกันมาเทียบด้วย (กันตัดเทคใหม่ทิ้งแล้วเก็บเทคเก่า)
            SA, q = S, j + 1
            while q < len(items) and q <= j + 5 and items[q]["start"] - items[j]["start"] < 15:
                SA += items[q]["t"]; q += 1
            hit = None
            for i in range(j - 1, max(-1, j - 1 - back), -1):
                if not keep[i] or items[j]["start"] - items[i]["start"] > window:
                    break
                ti = items[i]["t"]
                ctx = "".join(items[q]["t"] for q in range(i, j))
                for p in range(len(ti) - 1, -1, -1):
                    if ti[p] != S[0]:
                        continue
                    T = ctx[p:p + L]
                    # เริ่มจากกลางวรรคต้องคล้ายกันมากกว่า กันจับคู่มั่ว เช่น "ค[น]เสียสติ" กับ "[น]้ำเสียง..."
                    if len(T) < 3 or ratio(SA[:max(len(T), 4)], T) < (mid_thresh if p > 0 else thresh):
                        continue
                    A = ctx[p:]
                    if p > 0 and len(A) < min_tail and A not in _DANGLING:
                        continue  # คำสั้นท้ายวรรคที่บทตั้งใจพูดซ้ำ เช่น "แต่พวกเขากลัว / กลัวว่า..."
                    if ratio(A, SA[:len(A) + pad]) >= abandon:
                        hit = (i, p); break
                if hit:
                    break
            if hit:
                i, p = hit
                u = items[i]
                if u.get("ct") and p < len(u["ct"]) and len(u["t"]) - p < min_tail:  # คำท้ายสั้นๆ ("ไม่") ต้องแม่น
                    t0 = u["ct"][p]  # เวลาจริงจาก Whisper (แม่นกว่าการประมาณตามสัดส่วนตัวอักษร)
                else:
                    t0 = u["start"] + (u["end"] - u["start"]) * p / max(1, len(u["t"]))
                if p > 0:
                    t0 = max(u["start"], t0 - 0.05)
                dropped = "".join(items[q]["o"] for q in range(i, j))[p:]
                new.append((t0, items[j]["start"], "retake", dropped))
                for q in range(i + 1, j):
                    keep[q] = False
                if p == 0:
                    keep[i] = False
                else:
                    items[i] = dict(u, t=u["t"][:p], o=u["o"][:p], end=t0, ct=(u.get("ct") or [])[:p] or None)
            j += 1
        if not new:
            break
        cuts += new
        items = [it for it, k in zip(items, keep) if k]
    return sorted(cuts)

def detect_words(U, cuts, vs, e, L=8, window=12.0, max_back=80, thresh=0.75, abandon=0.6,
                 short=6, short_gap=0.2, min_gap=0.08, passes=3):
    """อ่านผิดแล้วต่อทันทีภายในวรรคเดียวกัน (ใช้เวลารายตัวอักษรจาก Whisper + ดึงจุดตัดไปที่ช่วงเงียบของ VAD)"""
    def dropped(t):
        return any(a <= t < b for a, b, *_ in cuts)
    C = []  # [char, start, end, first_of_utt]
    for u in U:
        if not u.get("words") or is_filler(u["text"], u["end"] - u["start"]):
            continue
        first = True
        for s, en, w in u["words"]:
            for ch, och in zip(canon(w), norm(w)):
                if not dropped(s):
                    C.append([ch, s, en, first, och]); first = False
    n_fr = len(vs)

    def snap(t, back=0.25, fwd=0.05):
        lo, hi = max(0, int((t - back) / HOP)), min(n_fr, int((t + fwd) / HOP) + 1)
        cand = [f for f in range(lo, hi) if not vs[f]]
        if cand:
            return min(cand, key=lambda f: abs(f * HOP - t)) * HOP
        lo, hi = max(0, int((t - 0.08) / HOP)), min(n_fr, int((t + 0.08) / HOP) + 1)
        return (lo + int(np.argmin(e[lo:hi]))) * HOP if hi > lo else t

    def gap_before(j):
        if j == 0 or C[j][3]:
            return 9.0
        g = C[j][1] - C[j - 1][2]
        f0, f1 = int(C[j - 1][2] / HOP), int(C[j][1] / HOP)
        if f1 > f0 and (~vs[f0:f1]).sum() >= 2:
            g = max(g, (~vs[f0:f1]).sum() * HOP)
        return g

    out = []
    for _ in range(passes):
        txt = "".join(c[0] for c in C)
        hits, j, drop = [], 1, set()
        while j < len(C) - 3:
            g = gap_before(j)
            if g < min_gap:
                j += 1; continue
            S = txt[j:j + L]
            hit = None
            for i in range(j - 2, max(-1, j - max_back), -1):
                if C[j][1] - C[i][1] > window:
                    break
                if txt[i] != S[0] or ratio(S, txt[i:i + L]) < thresh:
                    continue
                A = txt[i:j]
                if len(A) < short and g < short_gap:  # คำซ้ำสั้นๆ ไม่มีการหยุด = ภาษาปกติ เช่น "จริงจริง"
                    continue
                if ratio(A, txt[j:j + len(A) + 2]) >= abandon:  # ท่อนที่ถูกทิ้งทั้งท่อนต้องคล้ายต้นเทคใหม่
                    hit = i; break
            if hit is not None:
                t0, t1 = snap(C[hit][1]), snap(C[j][1])
                if t1 - t0 > 0.1:
                    hits.append((t0, t1, "retake", "".join(c[4] for c in C[hit:j])))
                    drop.update(range(hit, j))
                j += L
            else:
                j += 1
        if not hits:
            break
        out += hits
        C = [c for k, c in enumerate(C) if k not in drop]
    return out

# ---------------------------------------------------------------- isolated slips ("เผาโค้ง")
def isolated_candidates(U, cuts, max_chars=8, max_dur=1.0, min_gap=0.3):
    """วรรคสั้นที่ยืนเดี่ยวๆ มีช่วงเงียบคั่นหน้า-หลัง และยังไม่ถูกตัด"""
    out = []
    for i in range(1, len(U) - 1):
        u = U[i]
        if not u["text"].strip() or is_filler(u["text"], u["end"] - u["start"]):
            continue
        if (len(canon(u["text"])) <= max_chars and u["end"] - u["start"] <= max_dur
                and u["start"] - U[i - 1]["end"] >= min_gap and U[i + 1]["start"] - u["end"] >= min_gap
                and not _overlaps((u["start"], u["end"]), cuts)):
            out.append(u)
    return out

def detect_slips(x, U, cuts, model_name, max_logprob=-0.48):
    """คำหลุดเดี่ยวๆ ที่ไม่ซ้ำกับเทคไหน แยกจากคำจริง (เช่น "เหตุใด") ด้วยความมั่นใจของ Whisper:
    วัดกับไฟล์ที่คนตัด 2 ตอน: logprob < -0.48 คนตัดทิ้งทุกครั้ง (5/5), คำจริงได้ > -0.45"""
    cand = isolated_candidates(U, cuts)
    if not cand:
        return []
    segs = list(_run_part(get_pipe(model_name), x, [(u["start"], u["end"]) for u in cand], 8))
    out = []
    for u in cand:
        ss = [s for s in segs if u["start"] - 0.3 <= s.start <= u["end"]]
        if ss and float(np.mean([s.avg_logprob for s in ss])) < max_logprob:
            out.append((u["start"], u["end"], "หลุด", u["text"]))
    return out

# ---------------------------------------------------------------- user corrections (corrections.json)
def apply_corrections(src, cuts):
    """จุดที่ผู้ใช้ชี้มาแล้ว (corrections.json ข้างสคริปต์) บังคับตามนั้นเสมอเมื่อรันไฟล์เดิม:
    expect=cut -> ตัดช่วงนั้น, expect=keep -> เอาจุดตัดที่ทับช่วงนั้นออก
    ใช้กับกรณีที่ตัวจับอัตโนมัติทำไม่ได้ เช่น Whisper รวมสองรอบที่พูดซ้ำเป็นประโยคเดียว"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corrections.json")
    if not os.path.exists(path):
        return cuts
    C = json.load(open(path, encoding="utf-8"))
    keys = [k for k, f in C.get("files", {}).items()
            if os.path.exists(f["raw"]) and os.path.samefile(f["raw"], src)]
    if not keys:
        return cuts
    cases = [c for c in C.get("cases", []) if c["file"] in keys]
    out = list(cuts)
    for c in cases:
        if c["expect"] == "keep":
            k0, k1 = c["raw_start"] + 0.1, c["raw_end"] - 0.1
            out = [x for x in out if not (x[0] < k1 and k0 < x[1] and
                                           min(x[1], k1) - max(x[0], k0) > 0.5 * (k1 - k0))]
    for c in cases:
        if c["expect"] == "cut" and c.get("force"):
            out.append((c["raw_start"], c["raw_end"], "แก้ตามผู้ใช้", c["text"]))
    n = sum(1 for c in cases if c["expect"] == "cut" and c.get("force")) + sum(1 for c in cases if c["expect"] == "keep")
    print(f"  ใช้จุดแก้ไขจาก corrections.json: {n} จุด")
    return sorted(out)

# ---------------------------------------------------------------- review flags (จุดที่ควรฟังเช็ค)
def _overlaps(c, others):
    return any(o[0] < c[1] and c[0] < o[1] for o in others)

def _inner_repeats(U, k=4, win=30):
    """คำซ้ำกลางวรรค เช่น "สะท้อนแสงจันทร์ละ สะท้อนแสงจันทร์" (ข้ามคำซ้ำปกติอย่าง "จริงจริง")"""
    out = []
    for u in U:
        C = [(ch, s) for s, _e, w in (u.get("words") or []) for ch in canon(w)]
        txt = "".join(c[0] for c in C)
        j = k
        while j < len(txt) - k:
            i = txt.rfind(txt[j:j + k], max(0, j - win), j - 1)
            if i >= 0 and not (j - i == k or txt[i:j] == txt[j:j + (j - i)]):
                if C[j][1] - C[i][1] > 0.15:
                    out.append((C[i][1], C[j][1], "ซ้ำกลางวรรค", txt[i:j]))
                j += k
            else:
                j += 1
    return out

def review_points(U, cuts, vs, e):
    """แบ่งจุดที่ควรฟังเช็คเป็น 2 กลุ่ม:
    unsure  = จุดที่ตัดไปแต่ไม่มั่นใจ (เกณฑ์เข้มแล้วไม่ตัด หรือเป็นท่อนสั้น)
    suspect = จุดที่ไม่ได้ตัดแต่น่าสงสัย (เกณฑ์หลวมแล้วจะตัด, วรรคสั้นมาก, คำซ้ำกลางวรรค)
    วัดกับไฟล์ที่คนตัด: unsure ครอบคลุมจุดที่ตัดผิด ~70%, suspect ครอบคลุมคำผิดที่หลุด ~60%"""
    strict = detect(U, thresh=0.75, abandon=0.75, frag2=3)
    unsure = [c for c in cuts if c[2] in ("retake", "fragment") and
              (not _overlaps(c, strict) or c[1] - c[0] < 1.0 or c[2] == "fragment")]
    rel = detect(U, thresh=0.45, abandon=0.45, frag2=12, frag_sim=0.25, back=5)
    rel = rel + detect_words(U, rel, vs, e, thresh=0.6, abandon=0.45, short_gap=0.1)
    sus = [(a, b, "เกือบตัด", t) for a, b, _w, t in rel]
    for i, u in enumerate(U):
        if not u["text"].strip() or is_filler(u["text"], u["end"] - u["start"]):
            continue
        n = len(canon(u["text"]))
        gb = u["start"] - U[i - 1]["end"] if i > 0 else 9.0
        ga = U[i + 1]["start"] - u["end"] if i + 1 < len(U) else 9.0
        # คำหลุดเดี่ยวๆ เช่น "เผาโค้ง": สั้น และมีช่วงเงียบคั่นหน้า-หลัง (แยกจากคำจริงอย่าง "เหตุใด" ไม่ได้ จึงให้คนฟังตัดสิน)
        if n <= 6 or (n <= 8 and u["end"] - u["start"] <= 1.0 and gb >= 0.3 and ga >= 0.3):
            sus.append((u["start"], u["end"], "วรรคสั้น", u["text"]))
    sus += _inner_repeats(U)
    sus = sorted(c for c in sus if not _overlaps(c, cuts))
    merged = []  # รวมธงที่ซ้อนกัน
    for c in sus:
        if merged and c[0] <= merged[-1][1] + 0.3:
            p = merged[-1]; merged[-1] = (p[0], max(p[1], c[1]), p[2], p[3])
        else:
            merged.append(c)
    return sorted(set(unsure)), merged

# ---------------------------------------------------------------- script-guided retakes (--script)
def snap_gap(t, vs, e, back=0.25, fwd=0.05):
    """ดึงเวลาไปที่ช่วงเงียบ (VAD) ที่ใกล้ที่สุด ถ้าไม่มีใช้เฟรมที่เบาที่สุดในระยะ ±80ms"""
    n = len(vs)
    lo, hi = max(0, int((t - back) / HOP)), min(n, int((t + fwd) / HOP) + 1)
    cand = [f for f in range(lo, hi) if not vs[f]]
    if cand:
        return min(cand, key=lambda f: abs(f * HOP - t)) * HOP
    lo, hi = max(0, int((t - 0.08) / HOP)), min(n, int((t + 0.08) / HOP) + 1)
    return (lo + int(np.argmin(e[lo:hi]))) * HOP if hi > lo else t

def load_script(paths):
    """บทที่ผู้พากย์ใช้อ่าน (หลายไฟล์ต่อกันตามลำดับตอน) -> ข้อความ canonical"""
    return "".join(canon(open(p, encoding="utf-8-sig").read()) for p in paths)

def detect_script(U, S, vs, e, K=3, scale=150.0, min_ratio=0.45, max_jump=3000,
                  min_back=4, max_back_chars=250, max_cut_s=25.0):
    """เทียบเสียงที่ถอดได้กับบท: ถ้าตำแหน่งในบทถอยหลัง = ผู้พากย์ย้อนอ่านใหม่ -> ตัดเทคก่อนหน้า เก็บเทคสุดท้าย"""
    C = []  # [canon_char, start, utt_index, orig_char]
    for ui, u in enumerate(U):
        for s, _e, w in u.get("words") or []:
            for ch, och in zip(canon(w), norm(w)):
                C.append([ch, s, ui, och])
    idx = {}
    for b in range(len(S) - K + 1):
        idx.setdefault(S[b:b + K], []).append(b)
    by_u = {}
    for k, c in enumerate(C):
        by_u.setdefault(c[2], []).append(k)
    pos = np.full(len(C), -1)
    ptr, misses, span_end = 0, 0, len(C)
    for ui in sorted(by_u):
        if ptr >= len(S) - 80 or misses >= 8:  # อ่านจบบทแล้ว / เสียงหลุดออกนอกบท (เช่นตอนถัดไปที่ไม่มีบท)
            span_end = by_u[ui][0]
            break
        ks = by_u[ui]
        txt = "".join(C[k][0] for k in ks)
        votes = {}
        for a in range(len(txt) - K + 1):
            for b in idx.get(txt[a:a + K], ()):
                st = b - a
                if abs(st - ptr) <= max_jump:  # ใกล้ตำแหน่งที่อ่านถึงล่าสุดได้คะแนนมากกว่า
                    votes[st // 4] = votes.get(st // 4, 0) + 1.0 / (1 + abs(st - ptr) / scale)
        if not votes:
            misses += len(txt) >= 6; continue
        st = max(votes, key=votes.get) * 4
        lo, hi = max(0, st - 20), min(len(S), st + int(len(txt) * 1.3) + 20)
        blocks = [b for b in difflib.SequenceMatcher(None, txt, S[lo:hi], autojunk=False).get_matching_blocks() if b.size >= 2]
        if sum(b.size for b in blocks) / max(1, len(txt)) >= min_ratio:
            for b in blocks:
                for q in range(b.size):
                    pos[ks[b.a + q]] = lo + b.b + q
            ptr = int(max(pos[k] for k in ks if pos[k] >= 0)) + 1
            misses = 0
        elif len(txt) >= 6:
            misses += 1
    cuts, reached, hist = [], -1, []
    for k, p in enumerate(pos):
        if p < 0:
            continue
        if reached >= 0 and reached - max_back_chars <= p < reached - min_back:
            i = None
            for kk, pp in reversed(hist):
                if pp >= p:
                    i = kk
                else:
                    break
            if i is not None and C[k][1] - C[i][1] <= max_cut_s:
                t0, t1 = snap_gap(C[i][1], vs, e), snap_gap(C[k][1], vs, e)
                if t1 - t0 > 0.1:
                    cuts.append((t0, t1, "script", "".join(c[3] for c in C[i:k])))
                hist = [(kk, pp) for kk, pp in hist if kk < i]
                reached = hist[-1][1] if hist else -1
        hist.append((k, p))
        reached = max(reached, p)
    covered = (pos[:span_end] >= 0).sum() / max(1, span_end)  # วัดเฉพาะช่วงที่มีบท
    t_end = C[span_end - 1][1] if span_end else 0.0
    return cuts, covered, t_end

# ---------------------------------------------------------------- keep segments
def vad_mask(x, n_frames):
    """เฟรมที่เป็นเสียงพูดจริง (Silero VAD) - เสียงหายใจ/เสียงห้องจะไม่นับเป็นเสียงพูด"""
    from faster_whisper.vad import get_speech_timestamps, VadOptions
    m = np.zeros(n_frames, bool)
    for t in get_speech_timestamps(x, VadOptions(min_silence_duration_ms=100, speech_pad_ms=0)):
        m[int(t["start"] / SR / HOP):int(t["end"] / SR / HOP) + 1] = True
    return m

_EP_START = ("ตอนที่",)                                    # วรรคที่ขึ้นตอนใหม่
_EP_END = ("บ๊ายบาย", "จบตอนที่", "วิถีเซียน", "คําพี", "คัมภีร์")  # ปิดตอน / ชื่อเรื่อง

def _boundary_times(U):
    """เวลาที่เป็นรอยต่อตอน (ก่อน 'ตอนที่', หลัง 'บ๊ายบาย', รอบชื่อเรื่อง) - คนตัดเก็บช่วงหยุดยาวไว้ตรงนี้"""
    out = []
    for i, u in enumerate(U or []):
        t = norm(u["text"])
        if t.startswith(_EP_START):
            out.append(u["start"])
            if i + 1 < len(U):           # หลังเลขตอน/ชื่อตอน ก็หยุดนานเช่นกัน
                out.append(U[i + 1]["start"])
        if any(k in t for k in _EP_END):
            out.append(u["end"])
    return out

def keep_segments(n_frames, vs, e, cuts, max_pause=0.9, head=0.25, tail=0.2, U=None,
                  slope=0.25, cap=0.9, boundary_max=1.5, min_join=0.3, join_max=0.45):
    """เลือกช่วงที่เก็บ แล้วจัดจังหวะช่วงหยุดให้ฟังเป็นธรรมชาติ (ไม่ใช่ยาวเท่ากันหมด):
    - ช่วงหยุดสั้นกว่า max_pause: เก็บตามที่ผู้พากย์พูดจริง
    - ช่วงหยุดยาว: ย่อตามสัดส่วน (head+tail) + slope*(ส่วนที่เกิน) ไม่เกิน cap -> ที่เดิมยาวกว่ายังยาวกว่า
    - รอยต่อตอน (ก่อน 'ตอนที่', หลัง 'บ๊ายบาย'): เก็บได้ถึง boundary_max เหมือนคนตัด
    - รอยต่อหลังตัดเทคผิด: ให้มีช่วงหายใจอย่างน้อย min_join (ดึงช่วงเงียบเดิมกลับมา) กันคำชนกัน"""
    keep = np.ones(n_frames, bool)
    for a, b, *_ in cuts:
        keep[int(a / HOP):int(b / HOP)] = False
    cut = ~keep  # เสียงที่ตั้งใจตัดทิ้ง ห้ามดึงกลับมาตอนขยับจุดตัด
    # 1) รอยต่อที่ชิดเกินไป: ขยายช่วงที่เก็บเข้าไปในช่วงเงียบของส่วนที่ถูกตัด (ไม่ดึงเสียงพูดกลับมา)
    need = int(min_join / HOP)
    d = np.diff(np.concatenate([[1], keep.astype(int), [1]]))
    for a, b in zip(np.where(d == -1)[0], np.where(d == 1)[0]):  # ช่วงที่ถูกตัด [a, b)
        def sil_run(i, step):
            n = 0
            while 0 <= i < n_frames and not vs[i] and keep[i]:
                n += 1; i += step
            return n
        have = sil_run(a - 1, -1) + sil_run(b, 1)
        l, r = a, b - 1
        while have < need and (l < b or r >= a):
            grew = False
            if l < b and not vs[l] and l <= r:
                keep[l] = True; l += 1; have += 1; grew = True
            if have < need and r >= l and not vs[r]:
                keep[r] = True; r -= 1; have += 1; grew = True
            if not grew:
                break
    # 2) จัดช่วงหยุด (วัดในไทม์ไลน์หลังตัด เพราะการตัดอาจทำให้ช่วงเงียบสองช่วงมาต่อกัน)
    bounds = np.array(_boundary_times(U)) if U else np.array([])
    idx = np.where(keep)[0]
    s = ~vs[idx]
    d = np.diff(np.concatenate([[0], s.astype(int), [0]]))
    for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
        g = (b - a) * HOP
        if g <= min(max_pause, join_max):
            continue
        t0, t1 = idx[a] * HOP, idx[b - 1] * HOP
        is_join = a > 0 and np.any(np.diff(idx[a - 1:b + 1]) > 1)  # ช่วงเงียบนี้มีการตัดอะไรออกไปตรงกลาง
        if bounds.size and np.any((bounds >= t0 - 0.5) & (bounds <= t1 + 0.5)):
            target = min(g, boundary_max)
        elif is_join:
            target = min(g, max(min_join, join_max))  # คนตัดเหลือรอยต่อ ~0.4-0.46 วิ
        elif g <= max_pause:
            continue  # ช่วงหยุดปกติ เก็บตามที่ผู้พากย์พูดจริง
        else:
            target = min(cap, head + tail + slope * (g - max_pause))
        if target >= g:
            continue
        hh = int(target * head / (head + tail) / HOP) if a > 0 else 0
        tt = int(target / HOP) - hh
        keep[idx[a + hh:b - tt]] = False
    d = np.diff(np.concatenate([[0], keep.astype(int), [0]]))
    def quietest(f):
        return min(f, key=lambda k: e[min(k, n_frames - 1)])
    segs, last = [], 0
    for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
        # ขยับจุดตัดไปเฟรมที่เสียงเบาที่สุดในระยะ ±3 เฟรม ลดเสียงคลิก
        # แต่ขยายออกนอกท่อนได้เฉพาะเฟรมที่ไม่ได้ถูกตัด (เดิมดึงเสียงเทคผิดกลับมา 20-60 ms ติดอยู่ที่รอยต่อ)
        # และไม่ให้ทับกับท่อนก่อนหน้า (เสียงซ้ำ)
        fa = list(range(a, min(a + 4, b)))
        k = a - 1
        while a > 0 and k >= max(a - 3, last) and not cut[k]:
            fa.append(k); k -= 1
        fb = list(range(max(a + 1, b - 3), b + 1))
        k = b
        while b < n_frames and k < min(b + 3, n_frames) and not cut[k]:
            k += 1; fb.append(k)
        fa = [k for k in fa if k >= last] or [max(a, last)]
        a2 = a if a == 0 else quietest(fa)
        b2 = b if b >= n_frames else quietest(fb)
        if b2 > a2:
            segs.append((a2 * HOP, b2 * HOP))
            last = b2
    return segs

CRLF = chr(13) + chr(10)
EDL_HEADER = ('"ID";"Track";"StartTime";"Length";"PlayRate";"Locked";"Normalized";"StretchMethod";"Looped";'
              '"OnRuler";"MediaType";"FileName";"Stream";"StreamStart";"StreamLength";"FadeTimeIn";"FadeTimeOut";'
              '"SustainGain";"CurveIn";"GainIn";"CurveOut";"GainOut";"Layer";"Color";"CurveInR";"CurveOutR":'
              '"PlayPitch";"LockPitch";"FirstChannel";"Channels"')

FADE_MS = 8  # fade เข้า/ออกที่รอยต่อทุกจุด กันเสียงคลิก

def measure_lufs(path):
    """ความดังเฉลี่ย (Integrated LUFS) ของไฟล์"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.findall(r"I:\s*(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None

def edl_media_path(src):
    """VEGAS อ่าน EDL ด้วย code page ของ Windows (อังกฤษ) จึงอ่านชื่อไฟล์ภาษาไทยไม่ได้
    -> ใช้ชื่อสั้น 8.3 ถ้ามี ไม่งั้นสร้าง hard link ชื่ออังกฤษไว้ที่ <ไดรฟ์>\\cut_audio_media (ไม่เปลืองพื้นที่)"""
    import ctypes, hashlib, shutil
    p = os.path.abspath(src)
    if p.isascii():
        return p
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024) and buf.value.isascii():
        return buf.value
    folder = os.path.join(os.path.splitdrive(p)[0] + os.sep, "cut_audio_media")
    os.makedirs(folder, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", os.path.splitext(os.path.basename(p))[0]).strip("_") or "audio"
    tag = hashlib.md5(p.encode("utf-8")).hexdigest()[:6]
    link = os.path.join(folder, f"{stem}_{tag}{os.path.splitext(p)[1]}")
    if not os.path.exists(link):
        try:
            os.link(p, link)
        except OSError:
            shutil.copy2(p, link)  # ไดรฟ์ไม่รองรับ hard link -> ก๊อปแทน
    return link

def _edl_row(k, track, t, ln, rate, media, a, src_ms, gain, fade):
    return (f'{k}; {track}; {t:.4f}; {ln:.4f}; {rate:.6f}; FALSE; FALSE; 0; TRUE; FALSE; AUDIO; '
            f'"{media}"; 0; {a * 1000:.4f}; {src_ms:.4f}; {fade:.4f}; {fade:.4f}; {gain:.6f}; '
            f'4; 0.000000; 4; 0.000000; 0; -1; 4; 4; 0.000000; FALSE; 0; 0')

def write_edl(src, segs, path, rate, gain_db, unsure=(), suspect=()):
    """VEGAS EDL Text File: แทร็ก 1 = ท่อนที่เก็บ (เร็ว rate, fade สั้นๆ ที่รอยต่อ)
    แทร็ก 2 = เสียงที่ตัดไปแต่ไม่มั่นใจ / แทร็ก 3 = จุดน่าสงสัยที่ยังไม่ได้ตัด
    (แทร็ก 2-3 เสียงเบามาก -60 dB ไม่ดังทับ แต่เห็นเป็นกล่องบน timeline ตรงตำแหน่งที่ต้องเช็ค)
    ไฟล์เป็น ASCII ล้วน + CRLF เพราะ VEGAS อ่านด้วย code page ของ Windows
    นำเข้าใน VEGAS: File > Import > EDL Text File (*.txt)"""
    media = edl_media_path(src)
    gain = 10 ** (gain_db / 20)
    t, k, starts, lines = 0.0, 0, [], [EDL_HEADER]
    for a, b in segs:
        k += 1
        src_ms = (b - a) * 1000
        lines.append(_edl_row(k, 1, t, src_ms / rate, rate, media, a, src_ms, gain, FADE_MS))
        starts.append((a, b, t))
        t += src_ms / rate

    def out_ms(x):  # เวลาไฟล์ดิบ -> ตำแหน่งบน timeline (ms)
        for a, b, t0 in starts:
            if x < b:
                return t0 + max(0.0, x - a) * 1000 / rate
        return t
    for track, items in ((2, unsure), (3, suspect)):
        last_end = -1.0
        for r0, r1, *_ in sorted(items):
            src_ms = max(300.0, (r1 - r0) * 1000)
            pos = max(out_ms(r0), last_end)  # ไม่ให้กล่องในแทร็กเดียวกันซ้อนกัน
            k += 1
            lines.append(_edl_row(k, track, pos, src_ms / rate, rate, media, r0, src_ms, 0.001, 0))
            last_end = pos + src_ms / rate
    with open(path, "wb") as f:
        f.write((CRLF.join(lines) + CRLF).encode("ascii"))
    return media

def render(src, segs, out, tempo, gain_db, bitrate):
    """ตัดต่อด้วย numpy (fade เข้า/ออก FADE_MS ที่ทุกรอยต่อ) แล้วให้ FFmpeg เร่งความเร็ว/ปรับเสียง/เข้ารหัส"""
    import wave
    base = os.path.splitext(out)[0]
    wav_in, wav_out = base + ".tmp.in.wav", base + ".tmp.out.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-c:a", "pcm_s16le", wav_in], check=True)
    try:
        with wave.open(wav_in, "rb") as wi, wave.open(wav_out, "wb") as wo:
            ch, sr = wi.getnchannels(), wi.getframerate()
            wo.setnchannels(ch); wo.setsampwidth(2); wo.setframerate(sr)
            nf = int(sr * FADE_MS / 1000)
            ramp = np.sin(np.linspace(0, np.pi / 2, nf)) ** 2  # fade แบบนุ่ม
            for a, b in segs:
                s0, s1 = int(a * sr), int(b * sr)
                wi.setpos(min(s0, wi.getnframes()))
                y = np.frombuffer(wi.readframes(max(0, s1 - s0)), np.int16).reshape(-1, ch).astype(np.float32)
                m = min(nf, len(y) // 2)
                if m:
                    y[:m] *= ramp[:m, None]; y[-m:] *= ramp[:m][::-1, None]
                wo.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes())
        af = []
        if abs(tempo - 1) > 1e-6:
            af.append(f"atempo={tempo}")
        if gain_db:
            af.append(f"volume={gain_db:.2f}dB")
            if gain_db > 0:
                af.append("alimiter=limit=0.95")  # เพิ่มเสียงแล้วกันพีคแตก
        cmd = ["ffmpeg", "-y", "-v", "error", "-stats", "-i", wav_out]
        if af:
            cmd += ["-af", ",".join(af)]
        subprocess.run(cmd + ["-vn", "-c:a", "aac", "-b:a", bitrate, out], check=True)
    finally:
        for p in (wav_in, wav_out):
            if os.path.exists(p):
                os.remove(p)

def fmt(t):
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"

# ---------------------------------------------------------------- main
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma", ".opus")  # ไม่รวมวิดีโอ (.mp4) กันไปหยิบคลิปที่ทำเสร็จแล้ว
VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm")  # รับเฉพาะเมื่อลากไฟล์นั้นมาเอง (ไม่หยิบจากโฟลเดอร์)
DONE_TAG = "(ตัดเสียงแล้ว)"
DONE_RE = re.compile(r"\(\s*ตัด.*แล้ว\s*\)")  # จับชื่อที่สะกดต่างกันได้ด้วย เช่น "(ตัดเสีบงแล้ว)"

def expand_inputs(items, recursive=False):
    """รับไฟล์ / โฟลเดอร์ / wildcard (*.mp3) แล้วคืนรายการไฟล์เสียงดิบ (ข้ามไฟล์ที่ตัดแล้ว)"""
    files = []
    for it in items:
        it = it.strip().strip('"')
        if os.path.isdir(it):
            # glob.escape: ชื่อโฟลเดอร์ที่มี [ ] เช่น "คซ [323]" ไม่ให้ถูกตีความเป็น wildcard
            pat = os.path.join(glob.escape(it), "**", "*") if recursive else os.path.join(glob.escape(it), "*")
            cand = sorted(glob.glob(pat, recursive=recursive))
            if not any(f.lower().endswith(AUDIO_EXT) for f in cand):
                print("ไม่มีไฟล์เสียงในโฟลเดอร์:", it)
        elif os.path.exists(it):  # ไฟล์ที่ลากมาเอง (ชื่อมี [ ] ก็ใช้ได้)
            cand = [it]
            if not it.lower().endswith(AUDIO_EXT + VIDEO_EXT):
                print(f"ข้าม (ไม่ใช่ไฟล์เสียงที่รองรับ {', '.join(AUDIO_EXT + VIDEO_EXT)}):", it)
            elif DONE_RE.search(os.path.basename(it)):
                print("ข้าม (เป็นไฟล์ที่ตัดเสียงแล้ว):", it)
        elif any(ch in it for ch in "*?["):
            cand = sorted(glob.glob(it, recursive=recursive))
            if not cand:
                print("ไม่พบไฟล์ที่ตรงกับ:", it)
        else:
            cand = []
            print("ไม่พบไฟล์:", it)
        for f in cand:
            ext_ok = f.lower().endswith(AUDIO_EXT) or (f == it and f.lower().endswith(VIDEO_EXT))
            if os.path.isfile(f) and ext_ok and not DONE_RE.search(os.path.basename(f)):
                if os.path.abspath(f) not in map(os.path.abspath, files):
                    files.append(f)
    return files

def output_path(src, out_dir=None):
    name = os.path.splitext(os.path.basename(src))[0] + f" {DONE_TAG}.mp4"
    return os.path.join(out_dir or os.path.dirname(os.path.abspath(src)), name)

def process(src, out, a):
    cache = os.path.splitext(out)[0] + ".transcript.json"
    t0 = time.time()

    print("[1/4] อ่านไฟล์เสียงและแบ่งวรรค")
    x = load_audio(src)
    sp, e = speech_mask(x)
    U = utterances(sp)
    print(f"  ความยาว {len(x) / SR / 60:.1f} นาที, {len(U)} วรรค")

    T = json.load(open(cache, encoding="utf-8")) if os.path.exists(cache) and not a.retranscribe else None
    if T and all("words" in u for u in T) and len(T) == len(U):
        print("[2/4] ใช้ผลถอดเสียงจากแคช", cache)
    else:
        print(f"[2/4] Whisper {a.model} ถอดเสียงทีละวรรค")
        T = transcribe(x, U, a.model)
        json.dump(T, open(cache, "w", encoding="utf-8"), ensure_ascii=False)

    print("[3/4] หาเทคที่อ่านผิด/คำค้าง/เสียงหายใจ")
    vs = vad_mask(x, len(e))
    cuts = detect(T)
    cuts = sorted(cuts + detect_words(T, cuts, vs, e))
    cuts = sorted(cuts + detect_slips(x, T, cuts, a.model))
    cuts = apply_corrections(src, cuts)
    if a.script:
        sc, cov, t_end = detect_script(T, load_script(a.script), vs, e)
        print(f"  เทียบกับบท: ใช้ได้ถึง {fmt(t_end)} ของไฟล์ดิบ, ช่วงนั้นเสียงตรงกับบท {100 * cov:.0f}%, พบการย้อนอ่าน {len(sc)} จุด")
        if cov < 0.3:
            print("  !! เสียงตรงกับบทน้อยมาก ตรวจว่าใส่บทถูกตอนไหม (ไม่ใช้ผลจากบท)")
        else:
            cuts = sorted(cuts + sc)
    segs = keep_segments(len(e), vs, e, cuts, a.max_pause, a.head, a.tail, U=T)
    kept = sum(b - a_ for a_, b in segs)
    base = os.path.splitext(out)[0]
    def out_time(t):  # เวลาไฟล์ดิบ -> เวลาบน timeline ผลลัพธ์ (หลังตัดและเร่ง)
        return sum(max(0.0, min(b, t) - a_) for a_, b in segs) / a.tempo
    with open(base + ".cuts.txt", "w", encoding="utf-8") as f:
        f.write("เวลาบน timeline ผลลัพธ์/VEGAS | เวลาในไฟล์ดิบ | ยาว | ประเภท | ข้อความที่ถูกตัด\n")
        for c0, c1, why, txt in cuts:
            f.write(f"{fmt(out_time(c0))} | {fmt(c0)} - {fmt(c1)} | {c1 - c0:5.2f}s | {why:8s} | {txt}\n")
    n = {k: sum(1 for c in cuts if c[2] == k) for k in ("retake", "script", "fragment", "filler", "หลุด")}
    print(f"  ตัดเทคซ้ำ {n['retake']} จุด (+จากบท {n['script']}), คำค้าง {n['fragment']}, คำหลุดเดี่ยว {n['หลุด']}, เสียงอุทาน {n['filler']}, ท่อนที่เก็บ {len(segs)}")
    print(f"  เหลือ {kept / 60:.1f} นาที -> หลังเร่ง {a.tempo}x = {kept / a.tempo / 60:.1f} นาที")

    gain = a.gain
    if gain is None:  # ปรับให้ทุกไฟล์ดังเท่ากันที่ --lufs (คนตัดได้ -20.2 LUFS)
        lufs = measure_lufs(src)
        gain = round(a.lufs - lufs, 2) if lufs is not None else 0.0
        print(f"  ความดังไฟล์ดิบ {lufs} LUFS -> ปรับ {gain:+.2f} dB ให้ได้ {a.lufs} LUFS")

    unsure, suspect = review_points(T, cuts, vs, e)
    with open(base + ".review.txt", "w", encoding="utf-8") as f:
        f.write("จุดที่ควรฟังเช็ค เรียงตามเวลาบน timeline ผลลัพธ์/VEGAS\n"
                "  [ตัดแล้ว?] = ตัดไปแล้วแต่ไม่มั่นใจ (VEGAS แทร็ก 2)   [ยังไม่ตัด?] = น่าสงสัยแต่ยังไม่ได้ตัด (VEGAS แทร็ก 3)\n\n")
        rows = [(out_time(c[0]), "ตัดแล้ว?  ", c) for c in unsure] + [(out_time(c[0]), "ยังไม่ตัด?", c) for c in suspect]
        for ot, tag, (c0, c1, why, txt) in sorted(rows):
            f.write(f"{fmt(ot)} | [{tag}] | {why:10s} | {txt}\n")
    print(f"  จุดที่ควรฟังเช็ค: ตัดแล้วแต่ไม่มั่นใจ {len(unsure)}, น่าสงสัยแต่ยังไม่ตัด {len(suspect)} -> {base}.review.txt")

    if a.edl:
        write_edl(src, segs, base + ".vegas.txt", a.tempo, gain, unsure, suspect)
        print("  EDL สำหรับ VEGAS:", base + ".vegas.txt")
    if a.no_render:
        print(f"เสร็จใน {time.time() - t0:.0f}s (ไม่ได้สร้างไฟล์เสียง)")
        return
    # ไฟล์เดิมเปิดค้างอยู่ใน VEGAS/โปรแกรมอื่น -> เขียนทับไม่ได้ ให้บันทึกเป็นชื่อใหม่แทน
    k = 2
    while os.path.exists(out):
        try:
            with open(out, "ab"):
                break
        except PermissionError:
            alt = f"{os.path.splitext(output_path(src, a.out_dir) if not a.output else a.output)[0]} ({k}).mp4"
            print(f"  ไฟล์ {os.path.basename(out)} ถูกเปิดค้างอยู่ -> บันทึกเป็น {os.path.basename(alt)}")
            out, k = alt, k + 1
    print("[4/4] FFmpeg ตัด/รวม ->", out)
    render(src, segs, out, a.tempo, gain, a.bitrate)
    print(f"เสร็จใน {time.time() - t0:.0f}s : {out}")

def main():
    ap = argparse.ArgumentParser(description="ตัดเสียงพากย์ดิบอัตโนมัติ (ตัดเทคอ่านผิด/คำค้าง/เสียงหลุด + ย่อช่วงเงียบ)")
    ap.add_argument("inputs", nargs="+", help="ไฟล์เสียง / โฟลเดอร์ / wildcard เช่น \"D:\\Bear Friends\\คซ\\*.mp3\"")
    ap.add_argument("-o", "--output", help="ชื่อไฟล์ผลลัพธ์ (ใช้ได้เมื่อมีไฟล์เดียว) ค่าเริ่มต้น: <ชื่อไฟล์> (ตัดเสียงแล้ว).mp4")
    ap.add_argument("--out-dir", help="โฟลเดอร์เก็บผลลัพธ์ (ค่าเริ่มต้น: โฟลเดอร์เดียวกับไฟล์ดิบ)")
    ap.add_argument("-r", "--recursive", action="store_true", help="ค้นในโฟลเดอร์ย่อยด้วย")
    ap.add_argument("--skip-done", action="store_true", help="ข้ามไฟล์ที่มีผลลัพธ์อยู่แล้ว")
    ap.add_argument("--script", nargs="+", metavar="บท.txt",
                    help="ไฟล์บทที่ผู้พากย์อ่าน (.txt) ใส่หลายไฟล์ตามลำดับตอนได้ ช่วยจับการอ่านซ้ำได้แม่นขึ้น")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--tempo", type=float, default=1.07, help="เร่งความเร็ว (คนตัดใช้ 1.07)")
    ap.add_argument("--lufs", type=float, default=-20.2, help="ความดังเป้าหมาย (คนตัดได้ -20.2 LUFS)")
    ap.add_argument("--gain", type=float, default=None, help="บังคับปรับเสียงเป็น dB แทนการวัดอัตโนมัติ")
    ap.add_argument("--max-pause", type=float, default=0.9, help="ช่วงไม่ได้พูด/หายใจ ยาวกว่านี้ (วิ) จะถูกย่อ")
    ap.add_argument("--head", type=float, default=0.25, help="เหลือช่วงเงียบหลังคำสุดท้าย (วิ)")
    ap.add_argument("--tail", type=float, default=0.2, help="เหลือช่วงเงียบก่อนคำถัดไป (วิ)")
    ap.add_argument("--no-edl", dest="edl", action="store_false", help="ไม่ต้องสร้าง EDL สำหรับ VEGAS")
    ap.add_argument("--no-render", action="store_true", help="สร้างแค่ EDL/รายการตัด ไม่ต้องสร้างไฟล์เสียง")
    ap.add_argument("--bitrate", default="192k")
    ap.add_argument("--retranscribe", action="store_true", help="ไม่ใช้แคชผลถอดเสียง")
    a = ap.parse_args()

    # ไฟล์ .txt ที่ใส่/ลากมาพร้อมเสียง = บทที่ผู้พากย์อ่าน (เรียงตามชื่อไฟล์ = ลำดับตอน)
    txts = sorted(p for p in a.inputs if p.lower().endswith(".txt") and os.path.isfile(p))
    if txts:
        a.script = (a.script or []) + txts
        a.inputs = [p for p in a.inputs if p not in txts]
        print("ใช้บท:", ", ".join(os.path.basename(p) for p in a.script))
    files = expand_inputs(a.inputs, a.recursive)
    if not files:
        print("ไฟล์ที่ได้รับ:", *(a.inputs or ["(ไม่มี มีแต่ไฟล์บท .txt)"]), sep="\n  ")
        sys.exit("ไม่พบไฟล์เสียงดิบ")
    if a.output and len(files) > 1:
        sys.exit("-o ใช้ได้เมื่อมีไฟล์เดียว ถ้าหลายไฟล์ให้ใช้ --out-dir")
    if a.out_dir:
        os.makedirs(a.out_dir, exist_ok=True)

    print(f"พบ {len(files)} ไฟล์")
    ok, fail, skip, T0 = [], [], [], time.time()
    for i, src in enumerate(files, 1):
        out = a.output or output_path(src, a.out_dir)
        print(f"\n===== [{i}/{len(files)}] {os.path.basename(src)}")
        if a.skip_done and os.path.exists(out):
            print("  มีผลลัพธ์แล้ว ข้าม:", out); skip.append(src); continue
        try:
            process(src, out, a); ok.append(out)
        except Exception as ex:
            print("  ผิดพลาด:", ex); fail.append(src)
    if len(files) > 1:
        print(f"\nสรุป: สำเร็จ {len(ok)}, ข้าม {len(skip)}, ผิดพลาด {len(fail)}  ({(time.time() - T0) / 60:.1f} นาที)")
        for f in fail:
            print("  ผิดพลาด:", f)
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
