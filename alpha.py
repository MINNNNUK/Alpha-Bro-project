import streamlit as st
from datetime import datetime, date
from collections import defaultdict
from typing import List, Dict, Any
import math
import html
import pandas as pd
import altair as alt

# ================== 페이지/테마 & 글로벌 스타일 ==================
st.set_page_config(page_title="Alpha Advisors – 맞춤 공고 추천", layout="wide")

st.markdown("""
<style>
:root{
  --muted:#94a3b8; --muted-2:#64748B; --line:#2a2f3a;
  --ok:#10B981; --warn:#F59E0B; --bad:#EF4444;
  --card:#0b0f16; --card-2:#0f141d;
}
.block-container{padding-top:1.2rem; padding-bottom:2rem;}

.chip, .badge{
  display:inline-block; border-radius:9999px; font-weight:600; font-size:12px;
  padding:2px 8px; line-height:1.2; border:1px solid transparent;
}
.chip.ok   { background: rgba(16,185,129,.12); color: var(--ok);   border-color: rgba(16,185,129,.35); }
.chip.warn { background: rgba(245,158,11,.12); color: var(--warn); border-color: rgba(245,158,11,.35); }
.chip.bad  { background: rgba(239,68,68,.12); color: var(--bad);   border-color: rgba(239,68,68,.35); }

.badge.approved{ background: rgba(16,185,129,.12); color: var(--ok);   border-color: rgba(16,185,129,.35); }
.badge.rejected{ background: rgba(239,68,68,.12); color: var(--bad);   border-color: rgba(239,68,68,.35); }
.badge.pending { background: rgba(100,116,139,.12); color: var(--muted-2); border-color: rgba(100,116,139,.35); }

.card{ border:1px solid var(--line); border-radius:14px; padding:12px 14px; background:linear-gradient(180deg, var(--card), var(--card-2)); }
.card + .card{ margin-top:10px; }

.meta-box{ color: var(--muted-2); font-size:12px; line-height:1.2; }
.meta-top{ font-weight:700; margin-bottom:4px; }
.meta-bottom{ display:flex; gap:8px; align-items:center; }
.meta-bottom .d{ color:var(--muted); }

/* 검수 코멘트 표 */
.c-table{ width:100%; border-collapse:collapse; border-top:1px solid var(--line); }
.c-table tr{ border-bottom:1px solid var(--line); }
.c-table td{ padding:10px 8px; vertical-align:middle; }
.c-col-title{ width:45%; }
.c-col-status{ width:12%; }

/* --- 월별 가로 타임라인 --- */
.h-wrap{ margin-top:6px; }
.h-toolbar{ display:flex; gap:10px; align-items:center; margin:6px 0 10px; }
.h-scroll{
  display:flex; gap:14px; overflow-x:auto; padding:6px 2px 12px;
  scroll-snap-type: x mandatory;
}
.h-month{
  min-width:260px; scroll-snap-align:start;
  border:1px solid var(--line); border-radius:12px; padding:10px 12px;
  background:linear-gradient(180deg, #0b0f16, #0e1118);
}
.h-title{ font-weight:800; color:#e5e7eb; margin-bottom:8px; font-size:13px; letter-spacing:.2px; }
.h-badge{ color:var(--muted-2); font-size:12px; margin-left:6px; }
.h-item{
  display:flex; align-items:center; gap:8px; margin:6px 0; border-radius:8px; padding:2px 0;
  text-decoration:none;
}
.h-item:hover{ background: rgba(255,255,255,.05); padding:6px; margin:2px -6px; }
.h-day{ font-weight:800; color:#e5e7eb; font-variant-numeric: tabular-nums; width:28px; text-align:right; }
.h-ttl{
  color:#e5e7eb; font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1;
}
.h-type{ flex:0 0 auto; }
.h-due{ color:var(--muted-2); font-size:11px; }
.h-count{ font-size:11px; color:var(--muted-2); margin-left:4px; }

/* 분기/월 카드(세로 격자) */
.q-header{ font-weight:800; font-size:14px; color:#e2e8f0; margin:24px 0 8px; letter-spacing:.2px; }
.month-grid{ display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
.month-card{ border:1px solid var(--line); border-radius:12px; padding:10px 12px; background:linear-gradient(180deg, #0b0f16, #0e1118);}
.month-title{ font-weight:700; color:#e5e7eb; margin-bottom:8px; font-size:13px; }
.item{ display:flex; align-items:center; gap:8px; margin:6px 0; }
.item .date{ color:var(--muted-2); font-size:12px; }
.item .title{ color:#e5e7eb; font-size:13px; }

/* 범례 */
.legend{ display:flex; gap:10px; align-items:center; color:var(--muted-2); font-size:12px; margin-top:6px; }
.legend .dot{ width:8px; height:8px; border-radius:9999px; display:inline-block; }
.dot-info{ background: rgba(245,158,11,.9);}
.dot-due{ background: rgba(239,68,68,.9);}
</style>
""", unsafe_allow_html=True)

# ================== 데이터 ==================
ANNS: List[Dict[str, Any]] = [
    {"id":"KS-2025-001","title":"2025년 초기창업패키지(마케팅)","agency":"중기부","source":"K-Startup","region":"전국","stage":"초기","yearsMax":3,"dueDate":"2025-09-05","infoSessionDate":"2025-08-25","qaDate":"2025-09-10","amountKRW":80000000,"allowedUses":["마케팅","인건비","시제품"],"keywords":["마케팅","제조","소비재"],"budgetBand":"중간","updateType":"신규","updatedAt":"2025-08-10","url":"https://www.k-startup.go.kr/#KS-2025-001"},
    {"id":"BZ-2025-044","title":"수출바우처(디자인/브랜딩)","agency":"○○지자체","source":"Bizinfo","region":"부산","stage":"성장","yearsMax":7,"dueDate":"2025-09-20","infoSessionDate":"2025-09-01","amountKRW":50000000,"allowedUses":["수출","컨설팅","브랜딩","마케팅"],"keywords":["수출","디자인","브랜딩"],"budgetBand":"중간","updateType":"연장","updatedAt":"2025-08-16","url":"https://www.bizinfo.go.kr/#BZ-2025-044"},
    {"id":"KS-2025-077","title":"데이터·AI 바우처","agency":"과기정통부","source":"K-Startup","region":"전국","stage":"초기","yearsMax":7,"dueDate":"2025-10-02","qaDate":"2025-09-10","amountKRW":120000000,"allowedUses":["R&D","컨설팅","인건비"],"keywords":["AI","데이터","SaaS"],"budgetBand":"대형","updateType":"신규","updatedAt":"2025-08-12","url":"https://www.k-startup.go.kr/#KS-2025-077"},
    {"id":"BZ-2025-091","title":"판로개척(온/오프 마케팅)","agency":"중기유통센터","source":"Bizinfo","region":"서울","stage":"초기","yearsMax":7,"dueDate":"2025-09-12","amountKRW":30000000,"allowedUses":["마케팅","전시회","수출"],"keywords":["이커","마케팅","브랜드"],"budgetBand":"소액","updateType":"조건변경","updatedAt":"2025-08-15","url":"https://www.bizinfo.go.kr/#BZ-2025-091"},
    {"id":"NT-2025-013","title":"국가 R&D 실증(헬스케어)","agency":"복지부","source":"NTIS","region":"전국","stage":"성장","yearsMax":7,"dueDate":"2025-10-20","amountKRW":300000000,"allowedUses":["R&D","임상","인건비"],"keywords":["헬스케어","바이오","AI"],"budgetBand":"대형","updateType":"신규","updatedAt":"2025-08-09","url":"https://www.ntis.go.kr/#NT-2025-013"},
]
W = {"keywords":40, "stage":15, "region":10, "budget":15, "use":20}

def default_clients():
    return {
        "A":{"profile":{"name":"A사","businessType":"법인","region":"서울","years":1,"stage":"초기","industry":"AI/데이터","keywords":["AI","데이터","SaaS","마케팅"],"preferredUses":["마케팅","R&D"],"preferredBudget":"중간"}, "reviews":{}, "roadmap":{}, "pinned":True},
        "B":{"profile":{"name":"B사","businessType":"법인","region":"부산","years":4,"stage":"성장","industry":"디자인","keywords":["디자인","브랜딩","수출"],"preferredUses":["수출","컨설팅"],"preferredBudget":"중간"}, "reviews":{}, "roadmap":{}},
        "C":{"profile":{"name":"C사","businessType":"개인","region":"경기","years":0,"stage":"예비","industry":"이커","keywords":["마케팅","브랜드"],"preferredUses":["마케팅"],"preferredBudget":"소액"}, "reviews":{}, "roadmap":{}},
        "D":{"profile":{"name":"D사","businessType":"법인","region":"대구","years":2,"stage":"초기","industry":"제조","keywords":["제조","시제품"],"preferredUses":["시제품","인건비"],"preferredBudget":"중간"}, "reviews":{}, "roadmap":{}},
        "E":{"profile":{"name":"E사","businessType":"법인","region":"서울","years":6,"stage":"성장","industry":"헬스케어","keywords":["헬스케어","AI"],"preferredUses":["R&D","임상"],"preferredBudget":"대형"}, "reviews":{}, "roadmap":{}},
    }

# ================== 유틸 ==================
def KRW(n: int) -> str:
    if n is None: return "-"
    return format(n, ",")

def days_until(d: str) -> int:
    try:
        return math.ceil((datetime.strptime(d, "%Y-%m-%d").date() - date.today()).days)
    except:
        return 0

def inter(a: List[str], b: List[str]) -> int:
    sa = {str(x).strip() for x in (a or [])}
    sb = {str(x).strip() for x in (b or [])}
    return len(sa & sb)

def label_from_score(score: int) -> str:
    if score >= 70: return "가능"
    if score >= 50: return "주의"
    return "불가"

def label_chip(label_text: str) -> str:
    cls = "ok" if label_text=="가능" else ("warn" if label_text=="주의" else "bad")
    return f"<span class='chip {cls}'>{label_text}</span>"

def status_badge(status: str) -> str:
    return f"<span class='badge {status}'>{'승인' if status=='approved' else ('반려' if status=='rejected' else '대기')}</span>"

def norm(v: int, min_v: int, max_v: int) -> float:
    c = max(min_v, min(max_v, v))
    den = (max_v - min_v) or 1
    return (c - min_v) / den

def format_short_kr(n: int) -> str:
    if n is None: return ""
    if n >= 100_000_000:
        e = n / 100_000_000
        r = round(e * 10) / 10
        s = str(int(r)) if float(r).is_integer() else f"{r:.1f}"
        return s + "억원"
    else:
        c = n / 10_000_000
        r = round(c * 10) / 10
        s = str(int(r)) if float(r).is_integer() else f"{r:.1f}"
        return s + "천만원"

def parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None

def month_key_from_date(dt: date) -> str:
    return f"{dt.year}-{dt.month:02d}" if dt else ""

def quarter_label(dt: date) -> str:
    if not dt: return ""
    q = (dt.month - 1)//3 + 1
    return f"Q{q} {dt.year}"

# ================== 매칭 ==================
def compute(profile: Dict[str, Any], anns: List[Dict[str, Any]], w: Dict[str, int]):
    results = []
    for a in anns:
        rationale = []
        years_ok = (a.get("yearsMax") is None) or (profile["years"] <= a.get("yearsMax"))
        rationale.append(f"업력 {profile['years']}년 ≤ {a.get('yearsMax','제한없음')}" if years_ok else f"업력 초과({profile['years']}>{a.get('yearsMax')})")

        stage_ok = (a["stage"] == profile["stage"]) or (a["stage"] == "초기" and profile["stage"] == "예비")
        rationale.append(f"단계 적합({profile['stage']}↔{a['stage']})" if stage_ok else f"단계 불일치({profile['stage']}↔{a['stage']})")

        region_ok = (a["region"] == "전국") or (profile["region"] in a["region"])
        rationale.append(f"지역 적합({profile['region']}⊆{a['region']})" if region_ok else f"지역 제한({a['region']})")

        kw = inter(profile["keywords"], a.get("keywords", []))
        rationale.append(f"키워드 교집합 {kw}" if kw > 0 else "키워드 교집합 없음")

        budget_ok = (a.get("budgetBand") is None) or (a.get("budgetBand") == profile.get("preferredBudget"))
        rationale.append(f"예산 선호({profile.get('preferredBudget')})" if budget_ok else f"예산 불일치({a.get('budgetBand')}≠{profile.get('preferredBudget')})")

        use_overlap = inter(profile.get("preferredUses", []), a.get("allowedUses", []))
        rationale.append(f"사용처 매칭 {use_overlap}" if use_overlap > 0 else "사용처 매칭 없음")

        score = (
            norm(kw, 0, max(3, len(profile["keywords"]))) * w["keywords"] +
            (w["stage"] if stage_ok else 0) +
            (w["region"] if region_ok else 0) +
            (w["budget"] if budget_ok else 0) +
            norm(use_overlap, 0, max(3, len(profile.get("preferredUses", [])))) * w["use"]
        )
        score = int(round(score))

        hard_fail = (not years_ok) or ((not region_ok) and a["region"] != "전국") or (kw == 0 and use_overlap == 0)
        lbl = "불가" if hard_fail else label_from_score(score)

        results.append({"ann": a, "score": score, "label": lbl, "rationale": rationale})
    return results

# ================== 세션 상태 ==================
if "clients" not in st.session_state:
    st.session_state.clients = default_clients()
if "active" not in st.session_state:
    st.session_state.active = "A"
if "search" not in st.session_state:
    st.session_state.search = ""
if "roadmap_df" not in st.session_state:
    st.session_state.roadmap_df = pd.DataFrame()

clients = st.session_state.clients
active = st.session_state.active

# ================== 사이드바 ==================
with st.sidebar:
    st.markdown("### Alpha Advisors")
    st.session_state.search = st.text_input("고객사 검색", st.session_state.search, placeholder="회사명으로 검색")

    def client_sorted_ids():
        filtered = [cid for cid in clients.keys() if st.session_state.search.lower() in clients[cid]["profile"]["name"].lower()]
        return sorted(filtered, key=lambda cid: ((0 if clients[cid].get("pinned") else 1), clients[cid]["profile"]["name"]))

    for cid in client_sorted_ids():
        mlist = sorted(compute(clients[cid]["profile"], ANNS, W), key=lambda x: x["score"], reverse=True)
        top1 = mlist[0] if mlist else None
        due = f"D-{max(0, days_until(top1['ann']['dueDate']))}" if (top1 and top1["ann"].get("dueDate")) else ""
        lbl = top1["label"] if top1 else "-"
        meta_html = f"""
        <div class='meta-box'>
          <div class='meta-top'>Top</div>
          <div class='meta-bottom'>
            {label_chip(lbl)}
            <span class='d'>{html.escape(due)}</span>
          </div>
        </div>
        """
        col1, col2, col3 = st.columns([5,5,2], vertical_alignment="center")
        with col1:
            if st.button(clients[cid]['profile']['name'], key=f"sel-{cid}", use_container_width=True):
                st.session_state.active = cid
                active = cid
        with col2:
            st.markdown(meta_html, unsafe_allow_html=True)
        with col3:
            pin_txt = "★" if clients[cid].get("pinned") else "☆"
            if st.button(pin_txt, key=f"pin-{cid}", help="핀 토글", use_container_width=True):
                clients[cid]["pinned"] = not clients[cid].get("pinned")
                st.session_state.clients = clients

# ================== 메인 ==================
C = clients[active]
matches = compute(C["profile"], ANNS, W)
top = sorted(matches, key=lambda x: x["score"], reverse=True)[:10]

header_col1, header_col2 = st.columns([7,3])
with header_col1:
    st.markdown(f"## {C['profile']['name']} – 맞춤 공고 추천 (Top-10)")
with header_col2:
    p = C["profile"]
    st.caption(f"{p['businessType']} • {p['stage']} • 업력 {p['years']}년 • {p['region']} • 키워드 {len(p['keywords'])}")

# ================== 추천 리스트 ==================
st.markdown("### 추천 목록")
for item in top:
    ann = item["ann"]
    score = item["score"]
    rlabel = item["label"]
    reviews = C.get("reviews", {})
    current_status = reviews.get(ann["id"], {}).get("status", "pending")
    current_comment = reviews.get(ann["id"], {}).get("comment", "")

    with st.expander(f"{ann['title']}"):
        top_cols = st.columns([5,3,2])
        with top_cols[0]:
            st.markdown(f"**{ann['agency']}** • {ann['source']} • {ann['region']}")
            if ann.get("url"):
                st.markdown(f"[공고 링크]({ann['url']})")
        with top_cols[1]:
            info_lines = []
            if ann.get("infoSessionDate"):
                info_lines.append(f"설명회: {ann['infoSessionDate']}")
            info_lines.append(f"마감: **{ann['dueDate']}** (D-{max(0, days_until(ann['dueDate']))})")
            st.write("\n\n".join(info_lines))
        with top_cols[2]:
            amt = ann.get("amountKRW")
            st.write(f"금액: ₩ {KRW(amt)} ({format_short_kr(amt)})" if amt is not None else "금액: -")
            uses = ", ".join(ann.get("allowedUses", [])[:3]) + ("…" if len(ann.get("allowedUses", [])) > 3 else "")
            st.caption(f"사용처: {uses}")

        st.markdown(f"{label_chip(rlabel)} &nbsp; **{score} 점**", unsafe_allow_html=True)

        def score_key(s: str) -> int:
            return 1 if any(k in s for k in ["적합","교집합","매칭","선호","허용"]) else 0
        top_reasons = sorted(item["rationale"], key=score_key, reverse=True)[:3]
        st.markdown("- " + "\n- ".join(top_reasons))

        act_col1, act_col2, act_col3 = st.columns([1.2,1.2,6])
        with act_col1:
            if st.button("승인", key=f"approve-{active}-{ann['id']}", type="primary"):
                C["reviews"][ann["id"]] = {"status": "approved", "comment": current_comment}
                st.session_state.clients = clients
        with act_col2:
            if st.button("반려", key=f"reject-{active}-{ann['id']}"):
                C["reviews"][ann["id"]] = {"status": "rejected", "comment": current_comment}
                st.session_state.clients = clients
        with act_col3:
            new_comment = st.text_input("코멘트", value=current_comment, key=f"cmt-{active}-{ann['id']}")
            if new_comment != current_comment:
                C["reviews"][ann["id"]] = {"status": C["reviews"].get(ann["id"], {}).get("status","pending"), "comment": new_comment}
                st.session_state.clients = clients

        st.markdown(status_badge(current_status), unsafe_allow_html=True)

st.divider()

# ================== 로드맵 자동생성 ==================
st.markdown("### 12개월 로드맵(마감/설명회)")

def build_roadmap_df(approved_anns: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for a in approved_anns:
        if a.get("infoSessionDate"):
            d = parse_date(a["infoSessionDate"])
            rows.append({
                "date": pd.to_datetime(d) if d else None,
                "type": "설명회",
                "title": a["title"],
                "agency": a.get("agency",""),
                "amountKRW": a.get("amountKRW"),
                "month": month_key_from_date(d) if d else "",
                "id": a["id"],
                "url": a.get("url","")
            })
        if a.get("dueDate"):
            d = parse_date(a["dueDate"])
            rows.append({
                "date": pd.to_datetime(d) if d else None,
                "type": "마감",
                "title": a["title"],
                "agency": a.get("agency",""),
                "amountKRW": a.get("amountKRW"),
                "month": month_key_from_date(d) if d else "",
                "id": a["id"],
                "url": a.get("url","")
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("date")
    return df

def generate_roadmap_from_approved():
    approved_anns = [x["ann"] for x in top if C.get("reviews", {}).get(x["ann"]["id"], {}).get("status") == "approved"]
    # 월별 카드용 구조
    month_map = defaultdict(list)
    for a in approved_anns:
        if a.get("dueDate"):
            month_map[a["dueDate"][:7]].append({"id":a["id"]+"-due", "title":a["title"], "type":"마감", "date":a["dueDate"]})
        if a.get("infoSessionDate"):
            month_map[a["infoSessionDate"][:7]].append({"id":a["id"]+"-info", "title":a["title"], "type":"설명회", "date":a["infoSessionDate"]})
    C["roadmap"] = dict(month_map)
    st.session_state.clients = clients

    # 타임라인용 DF
    st.session_state.roadmap_df = build_roadmap_df(approved_anns)

btn_cols = st.columns([1.5, 8.5, 1.5])
with btn_cols[0]:
    if st.button("자동 생성"):
        generate_roadmap_from_approved()
with btn_cols[2]:
    if not st.session_state.roadmap_df.empty:
        csv = st.session_state.roadmap_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("CSV 저장", csv, file_name=f"roadmap_{C['profile']['name']}.csv")

roadmap = C.get("roadmap", {})

# ===== 보기 방식 선택: 가로 타임라인(월별) / 점 플롯 =====
view = st.radio("타임라인 보기", ["가로 타임라인(월별 정렬)", "점 플롯(보조)"], index=0, horizontal=True)

# ===== 1) 가로 타임라인(월별 정렬) =====
if view.startswith("가로") and not st.session_state.roadmap_df.empty:
    df = st.session_state.roadmap_df.copy()

    # 필터
    with st.container():
        st.markdown("<div class='h-wrap'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2,2,6])
        with c1:
            types = st.multiselect("표시 구분", ["설명회","마감"], default=["설명회","마감"])
        with c2:
            show_d = st.checkbox("D-Day 표시", value=True)
        with c3:
            st.caption("← 좌우로 스크롤해 월별 공고를 한눈에 확인하세요.")

        if types:
            df = df[df["type"].isin(types)]

        # 월 정렬
        months = sorted(df["month"].dropna().unique(), key=lambda m: datetime.strptime(m, "%Y-%m"))
        # 가로 스크롤 렌더링
        html_blocks = ["<div class='h-scroll'>"]
        today = date.today()

        for m in months:
            sub = df[df["month"] == m].sort_values("date")
            count = len(sub)
            month_title = f"{m} <span class='h-badge'>· {count}건</span>"
            block = [f"<div class='h-month'><div class='h-title'>{month_title}</div>"]
            for _, row in sub.iterrows():
                d = row["date"].date() if pd.notna(row["date"]) else None
                day = f"{d.day:02d}" if d else "--"
                # 타입 칩 + D-Day
                chip = "<span class='chip warn'>설명회</span>" if row["type"]=="설명회" else "<span class='chip bad'>마감</span>"
                dday = ""
                if show_d and d:
                    dd = (d - today).days
                    # D-표시는 미래 기준만 강조
                    if dd >= 0:
                        dday = f"<span class='h-due'>&nbsp;D-{dd}</span>"
                # 링크 열기
                href = html.escape(row.get("url") or "#")
                block.append(
                    f"<a class='h-item' href='{href}' target='_blank' rel='noopener'>"
                    f"<span class='h-day'>{day}</span>"
                    f"<span class='h-ttl'>{html.escape(str(row['title']))}</span>"
                    f"<span class='h-type'>{chip}</span>"
                    f"{dday}"
                    f"</a>"
                )
            block.append("</div>")
            html_blocks.append("".join(block))
        html_blocks.append("</div>")
        st.markdown("".join(html_blocks), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif view.endswith("보조"):
    # ===== 2) 점 플롯(보조) =====
    if st.session_state.roadmap_df.empty and not roadmap:
        st.info("승인 후 **자동 생성** 버튼을 눌러 로드맵을 만드세요.")
    else:
        st.markdown("#### 연간 타임라인(점 플롯)")
        df = st.session_state.roadmap_df.copy()
        if not df.empty:
            today_df = pd.DataFrame({"today":[pd.to_datetime(date.today())]})
            base = alt.Chart(df)

            points = base.mark_circle(size=110).encode(
                x=alt.X("date:T", axis=alt.Axis(format="%b %d", title=None, labelAngle=-15)),
                y=alt.Y("type:N", sort=["설명회","마감"], title=None),
                tooltip=[
                    alt.Tooltip("type:N", title="구분"),
                    alt.Tooltip("title:N", title="공고"),
                    alt.Tooltip("agency:N", title="주관"),
                    alt.Tooltip("date:T", title="일자", format="%Y-%m-%d"),
                    alt.Tooltip("amountKRW:Q", title="금액", format=",.0f")
                ],
                color=alt.Color("type:N", legend=None)
            )

            today_rule = alt.Chart(today_df).mark_rule(strokeDash=[4,4]).encode(x="today:T")
            chart = (points + today_rule).properties(height=160, width="container")
            st.altair_chart(chart, use_container_width=True)
            st.markdown("""
            <div class='legend'>
              <span class='dot dot-info'></span> 설명회
              <span class='dot dot-due'></span> 마감
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption("표시할 타임라인 데이터가 없습니다. (승인 후 자동 생성 필요)")

# ===== 분기/월 카드 레이아웃(기존 세로 보기) =====
if roadmap:
    def first_day_of_month_key(k:str):
        try:
            y,m = k.split("-")
            return datetime(int(y), int(m), 1).date()
        except:
            return date.today()

    months_sorted = sorted(roadmap.keys(), key=first_day_of_month_key)
    quarter_groups: Dict[str, List[str]] = defaultdict(list)
    for m in months_sorted:
        dt = first_day_of_month_key(m)
        q = (dt.month - 1)//3 + 1
        quarter_groups[f"Q{q} {dt.year}"].append(m)

    for q in sorted(quarter_groups.keys(), key=lambda s: (int(s.split(" ")[1]), int(s[1]))):
        st.markdown(f"<div class='q-header'>{q}</div>", unsafe_allow_html=True)
        st.markdown("<div class='month-grid'>", unsafe_allow_html=True)
        for m in quarter_groups[q]:
            items = sorted(roadmap[m], key=lambda x: x["date"])
            month_html = [f"<div class='month-card'><div class='month-title'>{m}</div>"]
            for it in items:
                chip = "<span class='chip warn'>설명회</span>" if it['type']=="설명회" else "<span class='chip bad'>마감</span>"
                month_html.append(
                    f"<div class='item'>{chip}"
                    f"<span class='title'>{html.escape(it['title'])}</span>"
                    f"&nbsp;<span class='date'>{it['date']}</span></div>"
                )
            month_html.append("</div>")
            st.markdown("".join(month_html), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ================== 검수 코멘트 (테이블형) ==================
st.markdown("### 검수 코멘트")

rows_html = ["<table class='c-table'>"]
for item in top:
    ann = item["ann"]
    rev  = C.get("reviews", {}).get(ann["id"], {})
    status = rev.get("status", "pending")
    comment = html.escape(rev.get("comment", "—")) if rev.get("comment") else "—"
    rows_html.append(
        f"<tr>"
        f"<td class='c-col-title'>{html.escape(ann['title'])}</td>"
        f"<td class='c-col-status'>{status_badge(status)}</td>"
        f"<td class='c-col-comment'>{comment}</td>"
        f"</tr>"
    )
rows_html.append("</table>")
st.markdown("".join(rows_html), unsafe_allow_html=True)

# ================== 자체 테스트 ==================
def _self_tests():
    out = compute(default_clients()["A"]["profile"], ANNS, W)
    assert len(out) == len(ANNS), "Matches length"
    assert all(isinstance(x["score"], int) for x in out), "Scores numeric"
    assert format_short_kr(80_000_000)  == "8천만원"
    assert format_short_kr(120_000_000) == "1.2억원"
    assert format_short_kr(300_000_000) == "3억원"
    assert format_short_kr(50_000_000)  == "5천만원"
try:
    _self_tests()
except Exception as e:
    st.warning(f"Self-tests failed ⚠️ {e}")
