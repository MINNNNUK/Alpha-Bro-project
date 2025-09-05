# app.py — Alpha Advisors (Autoload, Fail-Safe)
import os, re, glob, html
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta

# -------------------------------------------------
# Page
# -------------------------------------------------
st.set_page_config(page_title="Alpha Advisors – 맞춤 공고 추천 (MVP)", page_icon="📈", layout="wide")
st.title("Alpha Advisors – 맞춤 공고 추천 (MVP)")
st.caption("업로드 없이도 ./data 폴더의 CSV/XLSX를 자동으로 읽어 실행합니다. (업로드는 선택)")

# -------------------------------------------------
# Paths / Candidates
# -------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

# (선택) 네 맥 경로들 — 여기에 파일이 있으면 자동 후보에 포함
ABS_CANDIDATES = [
    "/Users/minkim/git_test/kpmg-2025/ab_streamlit/2년치 공고 수집 (4).xlsx",
    "/Users/minkim/git_test/kpmg-2025/ab_streamlit/2025_통합공고 (4).xlsx",
    "/Users/minkim/git_test/kpmg-2025/ab_streamlit/알파 프로젝트 (6).xlsx",
]

# -------------------------------------------------
# IO helpers
# -------------------------------------------------
@st.cache_data
def read_table(path):
    """CSV 또는 XLSX를 DataFrame으로 읽기 (인코딩/확장자 자동)."""
    p = str(path)
    try:
        if p.lower().endswith((".xls", ".xlsx")):
            return pd.read_excel(p)
        # CSV: UTF-8 → CP949 순서로 시도
        try:
            return pd.read_csv(p, encoding="utf-8-sig")
        except Exception:
            return pd.read_csv(p, encoding="cp949")
    except Exception as e:
        raise e

def normalize_delimited(val):
    if pd.isna(val): return []
    s = re.sub(r"[,\t/;|]+", "|", str(val))
    parts = [p.strip() for p in s.split("|") if p.strip()]
    out, seen = [], set()
    for p in parts:
        if p not in seen:
            out.append(p); seen.add(p)
    return out

def find_col(df, candidates):
    cols = list(df.columns)
    low = [c.lower() for c in cols]
    for cand in candidates:
        if cand in low:
            return cols[low.index(cand)]
    for i, c in enumerate(low):
        for cand in candidates:
            if cand in c:
                return cols[i]
    return None

def to_date(val):
    if pd.isna(val): return ""
    s = str(val).strip()
    m = re.findall(r"(20\d{2}[-./]\d{1,2}[-./]\d{1,2})", s)
    if m:
        d = m[-1].replace(".", "-").replace("/", "-")
        try:
            y, mn, dd = [int(x) for x in d.split("-")]
            return f"{y:04d}-{mn:02d}-{dd:02d}"
        except: pass
    try:
        if re.fullmatch(r"\d{8}", s):  # yyyymmdd
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
        return pd.to_datetime(s).date().isoformat()
    except:
        return ""

def extract_amount_krw(val):
    if pd.isna(val): return np.nan
    s = str(val).replace(",", "")
    try:
        m = re.findall(r"(\d+(?:\.\d+)?)\s*억", s)
        if m: return int(float(m[0]) * 100_000_000)
        if "천만" in s:
            m = re.findall(r"(\d+(?:\.\d+)?)", s)
            if m: return int(float(m[0]) * 10_000_000)
        if "만" in s:
            m = re.findall(r"(\d+(?:\.\d+)?)", s)
            if m: return int(float(m[0]) * 1_000_000)
        m = re.findall(r"(\d{5,})", s)
        if m: return int(m[0])
    except: pass
    return np.nan

def budget_band(amount):
    if pd.isna(amount): return ""
    try:
        a = float(amount)
        if a >= 100_000_000: return "대형"
        if a >= 40_000_000: return "중간"
        return "소액"
    except: return ""

def inter(a, b):
    A = set([x.strip() for x in (a or []) if x])
    return sum(1 for x in (b or []) if x.strip() in A)

def dday(ds):
    if not ds: return ""
    try:
        return max(0, (pd.to_datetime(ds).date() - date.today()).days)
    except: return ""

# -------------------------------------------------
# Normalizers
# -------------------------------------------------
def normalize_announcements(df):
    df = df.copy()
    col = {}
    col["id"] = find_col(df, ["id","공고id","공고번호","ann_id"])
    col["title"] = find_col(df, ["title","공고명","사업명","과제명"])
    col["agency"] = find_col(df, ["agency","주관","부처","기관"])
    col["source"] = find_col(df, ["source","사이트","채널","출처"])
    col["region"] = find_col(df, ["region","지역"])
    col["stage"] = find_col(df, ["stage","단계","예비","초기","성장"])
    col["yearsMax"] = find_col(df, ["yearsmax","업력제한","업력","창업년도"])
    col["dueDate"] = find_col(df, ["duedate","마감","접수마감","접수 종료","접수기간"])
    col["infoSessionDate"] = find_col(df, ["설명회","오리엔테이션","사전설명회"])
    col["amountKRW"] = find_col(df, ["amountkrw","금액","지원금","한도","보조금"])
    col["allowedUses"] = find_col(df, ["alloweduses","사용처","지원분야","지원내용","바우처"])
    col["keywords"] = find_col(df, ["keywords","키워드","분야","산업","카테고리","태그"])
    col["budgetBand"] = find_col(df, ["budgetband","예산구간","지원규모"])
    col["updateType"] = find_col(df, ["updatetype","연장","재공고","조건변경","상태"])
    col["updatedAt"] = find_col(df, ["updatedat","업데이트","수정일"])
    col["url"] = find_col(df, ["url","링크","상세","웹사이트"])

    out = pd.DataFrame()
    out["id"] = df[col["id"]] if col["id"] else [f"AUTO-{i+1:04d}" for i in range(len(df))]
    out["title"] = df[col["title"]] if col["title"] else df.index.map(lambda i: f"공고 {i+1}")
    out["agency"] = df[col["agency"]] if col["agency"] else ""
    out["source"] = df[col["source"]] if col["source"] else ""
    out["region"] = (df[col["region"]] if col["region"] else "전국").fillna("전국")
    out["stage"] = (df[col["stage"]] if col["stage"] else "초기").fillna("초기")

    if col["yearsMax"]:
        out["yearsMax"] = df[col["yearsMax"]].map(lambda x: int(re.findall(r"(\d+)\s*년", str(x))[0]) if re.findall(r"(\d+)\s*년", str(x)) else np.nan)
    else:
        out["yearsMax"] = np.nan

    out["dueDate"] = (df[col["dueDate"]].map(to_date) if col["dueDate"] else "")
    out["infoSessionDate"] = (df[col["infoSessionDate"]].map(to_date) if col["infoSessionDate"] else "")
    out["amountKRW"] = df[col["amountKRW"]].map(extract_amount_krw) if col["amountKRW"] else np.nan
    out["allowedUses"] = df[col["allowedUses"]].map(normalize_delimited) if col["allowedUses"] else [[] for _ in range(len(df))]
    out["keywords"] = df[col["keywords"]].map(normalize_delimited) if col["keywords"] else [[] for _ in range(len(df))]
    out["budgetBand"] = df[col["budgetBand"]] if col["budgetBand"] else out["amountKRW"].map(budget_band)
    out["updateType"] = df[col["updateType"]] if col["updateType"] else ""
    out["updatedAt"] = df[col["updatedAt"]].map(to_date) if col["updatedAt"] else ""
    out["url"] = df[col["url"]] if col["url"] else ""
    return out.fillna({"agency":"", "source":"", "budgetBand":"", "updateType":"", "updatedAt":"", "url":""})

def normalize_companies(df):
    df = df.copy()
    col = {}
    col["name"] = find_col(df, ["name","회사명","기업명","고객사"])
    col["businessType"] = find_col(df, ["businesstype","기업형태","법인","개인"])
    col["region"] = find_col(df, ["region","소재지","지역"])
    col["years"] = find_col(df, ["years","업력","설립연차"])
    col["founded"] = find_col(df, ["설립","설립연월일","창업일"])
    col["stage"] = find_col(df, ["stage","단계","예비","초기","성장"])
    col["industry"] = find_col(df, ["industry","산업","업종","주요 산업"])
    col["keywords"] = find_col(df, ["keywords","키워드","강점","사업아이템","제품"])
    col["preferredUses"] = find_col(df, ["preferreduses","선호용도","용도","지원희망"])
    col["preferredBudget"] = find_col(df, ["preferbudget","예산","budget"])

    out = pd.DataFrame()
    out["name"] = df[col["name"]] if col["name"] else df.index.map(lambda i: f"회사{i+1}")
    out["businessType"] = (df[col["businessType"]] if col["businessType"] else "법인").fillna("법인")
    out["region"] = (df[col["region"]] if col["region"] else "서울").fillna("서울")

    if col["years"]:
        out["years"] = df[col["years"]].map(lambda x: pd.to_numeric(x, errors="coerce")).fillna(1).astype(int)
    else:
        if col["founded"]:
            def _years_from_found(x):
                try:
                    d = pd.to_datetime(str(x)).date()
                    return max(0, date.today().year - d.year)
                except: return 1
            out["years"] = df[col["founded"]].map(_years_from_found)
        else:
            out["years"] = 1

    out["stage"] = (df[col["stage"]] if col["stage"] else "").fillna("")
    def infer_stage(y, s):
        if s: return s
        try:
            y = int(y)
            if y <= 0: return "예비"
            if y <= 3: return "초기"
            return "성장"
        except: return "초기"
    out["stage"] = [infer_stage(y, s) for y, s in zip(out["years"], out["stage"])]

    out["industry"] = df[col["industry"]] if col["industry"] else ""
    out["keywords"] = df[col["keywords"]].map(normalize_delimited) if col["keywords"] else [[] for _ in range(len(df))]
    out["preferredUses"] = df[col["preferredUses"]].map(normalize_delimited) if col["preferredUses"] else [[] for _ in range(len(df))]
    out["preferredBudget"] = (df[col["preferredBudget"]] if col["preferredBudget"] else "중간").fillna("중간")
    return out.fillna("")

# -------------------------------------------------
# Discovery (무조건 찾는 버전)
# -------------------------------------------------
def discover_files_ci():
    """data/와 ABS_CANDIDATES에서 파일 수집 → 이름 기반으로 분류 + 전체 목록 반환"""
    files = []
    if os.path.isdir(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            full = os.path.join(DATA_DIR, f)
            if os.path.isfile(full) and os.path.splitext(f)[1].lower() in (".csv",".xlsx",".xls"):
                files.append(full)
    files += [p for p in ABS_CANDIDATES if os.path.exists(p)]

    def is_comp(basename):
        b = basename.lower()
        return any(k in b for k in ["companies","company","comp","고객사","기업"])
    def is_ann(basename):
        b = basename.lower()
        return any(k in b for k in ["ann","bizinfo","ks_","공고"])

    comp_files = [f for f in files if is_comp(os.path.basename(f))]
    ann_files  = [f for f in files if is_ann(os.path.basename(f))]
    return sorted(set(comp_files)), sorted(set(ann_files)), files

def load_companies_df(up_file=None):
    """업로드 > 이름매칭 > 컬럼추정 > 마지막엔 '아무 파일이나' 시도."""
    if up_file is not None:
        return normalize_companies(read_table(up_file))

    comp_files, ann_files, all_files = discover_files_ci()

    # 1) 이름 매칭 파일
    for f in comp_files:
        try:
            return normalize_companies(read_table(f))
        except Exception:
            continue

    # 2) 컬럼 기반 자동 추정(이름이 애매해도 '회사명' 계열이 있으면 고객사로 간주)
    for f in all_files:
        try:
            df = read_table(f)
            if find_col(df, ["name","회사명","기업명","고객사"]):
                return normalize_companies(df)
        except Exception:
            continue

    # 3) 최후의 보루: 첫 파일이라도 잡아서 시도 (경고 표시)
    if all_files:
        st.warning(f"⚠️ 고객사 파일명을 인식하지 못했습니다. 임시로 첫 파일을 고객사로 가정하여 로드합니다: {os.path.basename(all_files[0])}")
        try:
            return normalize_companies(read_table(all_files[0]))
        except Exception:
            pass

    raise FileNotFoundError("Companies 데이터 소스를 찾지 못했습니다. data/ 폴더에 고객사 CSV/XLSX를 넣고 파일명에 'companies' 또는 '고객사'를 포함시키세요.")

def load_announcements_df(up_file=None):
    if up_file is not None:
        return normalize_announcements(read_table(up_file))

    comp_files, ann_files, all_files = discover_files_ci()
    frames = []

    # 1) 이름 매칭되는 공고 파일들
    for f in ann_files:
        try:
            frames.append(read_table(f))
        except Exception:
            continue

    # 2) 공고-columns 추정 실패 시: 전 파일에서 읽기 가능한 것 모두 병합
    if not frames:
        for f in all_files:
            try:
                frames.append(read_table(f))
            except Exception:
                continue

    if frames:
        df = pd.concat(frames, ignore_index=True).drop_duplicates()
        return normalize_announcements(df)

    raise FileNotFoundError("Announcements 데이터 소스를 찾지 못했습니다. data/에 공고 CSV/XLSX를 넣고 파일명에 'ann'/'bizinfo'/'KS_' 또는 '공고'를 포함시키세요.")

# -------------------------------------------------
# Matching
# -------------------------------------------------
def compute(profile, anns, w):
    out = []
    for _, a in anns.iterrows():
        rs = []
        years_ok = True
        if not pd.isna(a.get("yearsMax")):
            try: years_ok = int(profile["years"]) <= int(a.get("yearsMax"))
            except: years_ok = True
        rs.append(f"업력 {'적합' if years_ok else '초과'}({profile['years']}≤{a.get('yearsMax','-')})")

        stage_ok = (a.get("stage","") == profile.get("stage","")) or (a.get("stage","") == "초기" and profile.get("stage","") == "예비")
        rs.append(f"단계 {'적합' if stage_ok else '불일치'}({profile.get('stage','')}↔{a.get('stage','')})")

        region_ok = (a.get("region","전국") == "전국") or (str(profile.get("region","")) in str(a.get("region","전국")))
        rs.append(f"지역 {'적합' if region_ok else '제한'}({profile.get('region','')}⊆{a.get('region','')})")

        kw = inter(profile.get("keywords",[]), a.get("keywords",[]))
        rs.append(f"{'키워드 교집합' if kw>0 else '키워드 없음'} {kw if kw>0 else ''}".strip())

        budget_ok = (not a.get("budgetBand")) or (a.get("budgetBand") == profile.get("preferredBudget",""))
        rs.append(f"{'예산 선호' if budget_ok else '예산 불일치'}({profile.get('preferredBudget','')})")

        use_overlap = inter(profile.get("preferredUses",[]), a.get("allowedUses",[]))
        rs.append(f"{'사용처 매칭' if use_overlap>0 else '사용처 없음'} {use_overlap if use_overlap>0 else ''}".strip())

        score = (
            (kw and (kw / max(3, len(profile.get('keywords',[])))) or 0) * w["keywords"] +
            (w["stage"] if stage_ok else 0) +
            (w["region"] if region_ok else 0) +
            (w["budget"] if budget_ok else 0) +
            (use_overlap and (use_overlap / max(3, len(profile.get('preferredUses',[])))) or 0) * w["use"]
        )
        score = int(round(score))
        hard_fail = (not years_ok) or ((not region_ok) and a.get("region","전국")!="전국") or (kw==0 and use_overlap==0)
        lbl = "불가" if hard_fail else ("가능" if score>=80 else ("주의" if score>=50 else "불가"))
        out.append({"ann": a, "score": score, "label": lbl, "rationale": rs})
    return out

def add_days(ds, n):
    try:
        d = pd.to_datetime(ds).date()
        return (d + timedelta(days=n)).isoformat()
    except: return ""

def money(n):
    if pd.isna(n) or n in [None,"","nan"]: return "-"
    try:
        n = int(float(n)); s = f"{n:,}"
        return f"{s} (약 {round(n/100_000_000,1)}억원)" if n>=100_000_000 else s
    except: return str(n)

def badge_style(kind="neutral"):
    color = {"ok":"#065f46","warn":"#92400e","bad":"#991b1b","neutral":"#334155"}[kind]
    bg = {"ok":"#d1fae5","warn":"#fef3c7","bad":"#fee2e2","neutral":"#f1f5f9"}[kind]
    bd = {"ok":"#a7f3d0","warn":"#fde68a","bad":"#fecaca","neutral":"#e2e8f0"}[kind]
    return f"padding:2px 6px;border-radius:6px;border:1px solid {bd};display:inline-block;font-size:12px;background:{bg};color:{color};"

def row_html(m):
    a = m["ann"]
    kind = "ok" if m["label"]=="가능" else ("warn" if m["label"]=="주의" else "bad")
    uses = ", ".join((a.get("allowedUses") or [])[:3])
    info = f"설명회 {a.get('infoSessionDate','')}" if a.get("infoSessionDate") else ""
    dday_str = f"D-{dday(a.get('dueDate'))}" if a.get("dueDate") else ""
    rationale_list = "".join([f"<li>{html.escape(r)}</li>" for r in m["rationale"][:3]])
    url = a.get("url","")
    link_html = f'<a href="{html.escape(url)}" target="_blank">공고 링크</a>' if url else ""
    return f"""
    <tr>
      <td style="vertical-align:top;"><span style="{badge_style(kind)}">{m['label']} • {m['score']}</span></td>
      <td style="vertical-align:top;">
        <div><strong>{html.escape(str(a.get('title','')))}</strong></div>
        <div style="color:#475569;font-size:12px;">{html.escape(str(a.get('agency','')))} • {html.escape(str(a.get('source','')))} • {html.escape(str(a.get('region','')))}</div>
        <div style="font-size:12px;">{link_html}</div>
      </td>
      <td style="vertical-align:top;"><ul>{rationale_list}</ul></td>
      <td style="vertical-align:top;font-size:12px;">
        {'<div>📅 '+info+'</div>' if info else ''}
        <div><strong>마감 {a.get('dueDate','')}</strong></div>
        <div style="color:#475569;">{dday_str}</div>
      </td>
      <td style="vertical-align:top;font-size:12px;">
        <div>₩ {money(a.get('amountKRW'))}</div>
        <div style="color:#475569;">{html.escape(uses)}</div>
      </td>
    </tr>
    """

# -------------------------------------------------
# Sidebar – Upload(선택) + Weights + Debug
# -------------------------------------------------
with st.sidebar:
    st.header("1) 데이터 소스 (업로드는 선택)")
    up_comp = st.file_uploader("Companies CSV/XLSX", type=["csv","xlsx","xls"], key="up_comp")
    up_anns = st.file_uploader("Announcements CSV/XLSX", type=["csv","xlsx","xls"], key="up_anns")

    st.markdown("---")
    st.header("2) 가중치 (W)")
    w = {
        "keywords": st.slider("키워드", 0, 60, 40, 1),
        "stage": st.slider("단계", 0, 30, 15, 1),
        "region": st.slider("지역", 0, 30, 10, 1),
        "budget": st.slider("예산", 0, 30, 15, 1),
        "use": st.slider("사용처", 0, 30, 20, 1),
    }
    show_blocked = st.checkbox("불가 포함 보기", value=False)

    # Debug: 무엇을 찾았는지 확인
    comp_candidates, ann_candidates, all_files = [], [], []
    try:
        comp_candidates, ann_candidates, all_files = discover_files_ci()
    except Exception:
        pass
    with st.expander("🔎 자동탐색 결과"):
        st.write({"companies_candidates": comp_candidates,
                  "ann_candidates": ann_candidates,
                  "all_files": all_files})

# -------------------------------------------------
# Load Data (무조건 로드)
# -------------------------------------------------
companies = load_companies_df(up_comp)
anns = load_announcements_df(up_anns)

# 리스트형 보정
for col in ["keywords","allowedUses"]:
    if col in anns.columns and len(anns)>0 and not isinstance(anns[col].iloc[0], list):
        anns[col] = anns[col].apply(normalize_delimited)
for col in ["keywords","preferredUses"]:
    if col in companies.columns and len(companies)>0 and not isinstance(companies[col].iloc[0], list):
        companies[col] = companies[col].apply(normalize_delimited)

# -------------------------------------------------
# UI – Company select + Top-10
# -------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.header("3) 고객사 선택")
    comp_name = st.selectbox("고객사", companies["name"].astype(str).tolist())

C = companies.loc[companies["name"]==comp_name].iloc[0].to_dict()
st.subheader(f"🎯 {C['name']} – 맞춤 추천 Top-10")
st.write(f"{C.get('businessType','')} • {C.get('stage','')} • 업력 {C.get('years','?')}년 • {C.get('region','')}")

matches = compute(C, anns, w)
matches_use = matches if show_blocked else [m for m in matches if m["label"]!="불가"]
matches_sorted = sorted(matches_use, key=lambda m: (-m["score"], m["ann"].get('dueDate') or '9999-99-99'))
top = matches_sorted[:10]

if len(top)==0:
    st.info("추천 결과가 없습니다. (데이터/가중치 확인)")
else:
    rows = "\n".join(row_html(m) for m in top)
    st.markdown(f"""
    <div style="border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;">
      <table style="width:100%;font-size:14px;">
        <thead style="background:#f8fafc;text-align:left;">
          <tr>
            <th style="padding:8px;width:100px;">라벨·점수</th>
            <th style="padding:8px;">공고</th>
            <th style="padding:8px;width:340px;">사유(요약)</th>
            <th style="padding:8px;width:160px;">일정</th>
            <th style="padding:8px;width:180px;">금액/사용처</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# Roadmap
# -------------------------------------------------
st.markdown("---")
st.subheader("📅 12개월 로드맵 자동 생성")
if st.button("로드맵 자동 생성"):
    selected = [m["ann"] for m in top]
    board = {}
    def key(d): return d[:7] if d else ""
    for _, a in pd.DataFrame(selected).iterrows():
        if a.get("infoSessionDate"):
            board.setdefault(key(a["infoSessionDate"]), []).append({"type":"설명회","title":a["title"],"date":a["infoSessionDate"]})
        if a.get("dueDate"):
            for t, dd in [("초안",-14),("검토",-7),("마감",0),("발표",21),("정산",45)]:
                d2 = add_days(a["dueDate"], dd)
                if d2:
                    board.setdefault(key(d2), []).append({"type":t,"title":a["title"],"date":d2})
    st.session_state["board"] = board

board = st.session_state.get("board", {})
if board:
    for mth in sorted(board.keys()):
        st.markdown(f"**{mth}**")
        st.dataframe(pd.DataFrame(board[mth]), use_container_width=True)
else:
    st.caption("버튼을 눌러 로드맵을 생성하세요.")
