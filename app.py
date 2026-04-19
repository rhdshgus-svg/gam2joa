import streamlit as st
from google import genai
from google.genai import types
import datetime, re, math, time
import markdown

# 📱 모바일 최적화 및 딥 네이비/웜 골드 브랜드 테마 적용
st.set_page_config(page_title="솔 운명상점 Lite Premium", layout="centered", initial_sidebar_state="collapsed")
MODEL_NAME = 'gemini-2.5-pro'

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("API 키 설정 오류를 확인해주세요.")
    st.stop()

# ==========================================
# ⚙️ 1. 사주 명식 계산 엔진 (기존의 정교한 로직 유지)
# ==========================================
def get_sun_longitude(year, month, day, hour, minute):
    try: dt = datetime.datetime(year, month, day, hour, minute) - datetime.timedelta(hours=9)
    except ValueError: return 0
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t**2
    m_anomaly = 357.52911 + 35999.05029 * t - 0.0001537 * t**2
    m_rad = math.radians(m_anomaly)
    c = (1.914602 - 0.004817 * t - 0.000014 * t**2) * math.sin(m_rad)
    c += (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
    c += 0.000289 * math.sin(3 * m_rad)
    return (l0 + c) % 360.0

def calculate_saju(d_str, t_str):
    try:
        dp = re.findall(r'\d+', d_str)
        if len(dp)==1 and len(dp[0])==8: y, m, d = int(dp[0][:4]), int(dp[0][4:6]), int(dp[0][6:])
        else: return None
        tp = re.findall(r'\d+', t_str)
        hr = int(tp[0]) if len(tp)>0 else 0
        mn = int(tp[1]) if len(tp)>1 else 0
        stems, branches = ["갑","을","병","정","무","기","경","신","임","계"], ["자","축","인","묘","진","사","오","미","신","유","술","해"]
        lon = get_sun_longitude(y, m, d, hr, mn)
        adjusted_lon = (lon - 315.0) % 360.0
        month_idx = int(adjusted_lon // 30.0) 
        sy = y - 1 if month_idx == 11 or (m <= 2 and month_idx > 9) else y
        y_s, y_b = (sy - 4) % 10, (sy - 4) % 12
        yp = stems[y_s] + branches[y_b]
        m_b = (month_idx + 2) % 12
        m_s_start = {0:2, 1:4, 2:6, 3:8, 4:0, 5:2, 6:4, 7:6, 8:8, 9:0}[y_s]
        m_s = (m_s_start + month_idx) % 10
        mp = stems[m_s] + branches[m_b]
        dt = datetime.date(y, m, d)
        tv = hr * 60 + mn
        if tv >= 1410: dt += datetime.timedelta(days=1)
        d_idx = (dt.toordinal() - 693586) % 60
        ds, db = d_idx % 10, d_idx % 12
        dp_str = stems[ds] + branches[db]
        hb, limits = 0, [90, 210, 330, 450, 570, 690, 810, 930, 1050, 1170, 1290, 1410]
        for i, limit in enumerate(limits):
            if tv < limit: hb = i; break
        hs_start = {0:0, 1:2, 2:4, 3:6, 4:8, 5:0, 6:2, 7:4, 8:6, 9:8}[ds]
        hp = stems[(hs_start + hb) % 10] + branches[hb]
        return f"{yp}년 {mp}월 {dp_str}일 {hp}시"
    except: return None

def call_gemini(prompt):
    res = client.models.generate_content(
        model=MODEL_NAME, 
        contents=prompt, 
        config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=4096)
    )
    return res.text.strip()

# ==========================================
# 🎨 2. 프리미엄 HTML/CSS (다운로드용)
# ==========================================
PREMIUM_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
body { background-color: #f4f4f5; margin: 0; padding: 10px; color: #111; line-height: 1.6; }
.report-container { max-width: 600px; margin: 0 auto; background-color: #FFFFFF; padding: 25px 15px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.08); border-top: 6px solid #0A192F; }

/* 브랜드 헤더 (해와 소나무 모티브) */
.brand-header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #E2E8F0; }
.brand-header h1 { font-size: 26px; font-weight: 900; margin: 0; color: #0A192F; letter-spacing: -0.5px; }
.brand-header h1 span { color: #D4AF37; }
.brand-header p { font-size: 13px; color: #718096; margin: 8px 0 0 0; font-weight: 500; }
.saju-info { display: inline-block; background-color: #F8FAFC; color: #0A192F; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 700; border: 1px solid #E2E8F0; margin-top: 15px; }

/* 챕터 디자인 (아코디언 형태 시뮬레이션) */
.chapter { margin-bottom: 20px; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; }
.chapter-title { background-color: #0A192F; color: #FFFFFF; font-size: 16px; font-weight: 700; padding: 12px 15px; margin: 0; display: flex; align-items: center; }
.chapter-title::before { content: '✦'; color: #D4AF37; margin-right: 8px; font-size: 14px; }
.chapter-content { padding: 15px; background-color: #FFFFFF; font-size: 15px; }

/* 형광펜 핵심 요약 박스 */
blockquote { background-color: #FFFDF5; border-left: 4px solid #D4AF37; padding: 12px 15px; margin: 0 0 15px 0; border-radius: 4px; font-weight: 700; color: #0A192F; font-size: 15px; box-shadow: 0 1px 3px rgba(212, 175, 55, 0.1); }
blockquote p { margin: 0; }

h3 { display: none; } /* 마크다운 H3 숨김 처리 (커스텀 타이틀 사용) */
p { margin-top: 0; margin-bottom: 15px; color: #333; text-align: justify; word-break: keep-all; }
strong { color: #0A192F; font-weight: 800; background: linear-gradient(to top, rgba(212, 175, 55, 0.3) 30%, transparent 30%); }

.footer { text-align: center; margin-top: 40px; font-size: 12px; color: #A0AEC0; }
</style>
"""

# ==========================================
# 🚀 3. Streamlit UI
# ==========================================
st.markdown("""
    <style>
    div[data-testid="stAppViewBlockContainer"] { padding-top: 2rem; padding-bottom: 2rem; }
    .stButton>button { background-color: #0A192F; color: #D4AF37; font-weight: bold; border-radius: 8px; height: 55px; border: none; font-size: 16px; }
    .stButton>button:hover { background-color: #112A4F; color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #0A192F; font-weight: 900;'>솔 운명상점 <span style='color: #D4AF37;'>Lite Premium</span></h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 14px;'>바쁜 샵 환경에 맞춘 초고속 VIP 리포트 생성기</p>", unsafe_allow_html=True)

mode = st.radio("상담 모드 선택", ["👤 개인 분석", "💞 시너지(궁합) 분석"], horizontal=True)

st.markdown("### 📝 고객 1 정보")
col1, col2 = st.columns(2)
with col1: name1 = st.text_input("이름", key="n1")
with col2: gender1 = st.selectbox("성별", ["여성", "남성"], key="g1")
col3, col4 = st.columns(2)
with col3: birth1 = st.text_input("생년월일 (예: 19800101)", key="b1")
with col4: time1 = st.text_input("태어난 시간 (예: 14:30)", key="t1", placeholder="모르면 빈칸")

if mode == "💞 시너지(궁합) 분석":
    st.markdown("---")
    st.markdown("### 📝 고객 2 정보")
    col5, col6 = st.columns(2)
    with col5: name2 = st.text_input("이름", key="n2")
    with col6: gender2 = st.selectbox("성별", ["남성", "여성"], key="g2")
    col7, col8 = st.columns(2)
    with col7: birth2 = st.text_input("생년월일", key="b2")
    with col8: time2 = st.text_input("태어난 시간", key="t2", placeholder="모르면 빈칸")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("✨ 프리미엄 리포트 10초 쾌속 생성", use_container_width=True):
    if not name1 or not birth1:
        st.warning("기본 정보를 입력해주세요.")
    else:
        with st.spinner("AI 엔진이 데이터를 분석하고 있습니다... (약 10초 소요)"):
            saju1 = calculate_saju(birth1, time1)
            
            if mode == "👤 개인 분석":
                # 8개 챕터를 한 번의 프롬프트로 생성 (속도와 퀄리티 동시 확보)
                prompt = f"""
                고객: {name1} ({gender1}), 명식: {saju1}
                너는 명리학과 심리학에 능통한 최고급 컨설턴트야. 고객에게 제공할 8챕터 분량의 프리미엄 분석 리포트를 작성해.
                문체는 정중하고 세련된 평문(해요체/하십시오체)을 사용하고, 훈계나 불필요한 한자는 빼.
                
                [작성 규칙 - 매우 중요]
                각 챕터는 반드시 아래의 마크다운 형식을 정확히 지켜서 출력해.
                ### 챕터명
                > **핵심 요약:** (이곳에 1~2줄로 시선을 끄는 임팩트 있는 요약 작성)
                (이곳에 2~3문단으로 이루어진 깊이 있되 간결한 상세 설명 작성. 가독성을 위해 줄바꿈 잘할 것)

                [작성할 8개 챕터 목록]
                1. 코어 에너지 (타고난 본성과 매력)
                2. 자본의 그릇 (재물운의 크기와 돈이 새는 곳)
                3. 숨겨진 무기 (남들은 모르는 나만의 천재성)
                4. 대인 관계망 (내게 득이 되는 사람과 독이 되는 사람)
                5. 비즈니스 포지션 (직장/사업에서 성공률이 가장 높은 역할)
                6. 헬스케어 (선천적으로 취약한 건강 포인트)
                7. 2026-2027 기상도 (향후 2년간의 굵직한 운세 흐름)
                8. 마스터의 조언 (내일 당장 실천할 단 하나의 개운법)
                """
                raw_text = call_gemini(prompt)
                
                # 생성된 마크다운을 챕터별 HTML로 예쁘게 파싱
                chapters_html = ""
                parts = raw_text.split("###")
                for part in parts:
                    if part.strip():
                        lines = part.strip().split("\n", 1)
                        if len(lines) > 1:
                            title = lines[0].strip()
                            content = markdown.markdown(lines[1].strip())
                            chapters_html += f"<div class='chapter'><h2 class='chapter-title'>{title}</h2><div class='chapter-content'>{content}</div></div>"
                
                html_export = f"""
                <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="utf-8">{PREMIUM_CSS}</head>
                <body>
                <div class="report-container">
                    <div class="brand-header">
                        <h1>솔 <span>운명상점</span></h1>
                        <p>해처럼 굳건하게, 소나무처럼 푸르게</p>
                        <div class="saju-info">{name1}님의 VVIP 리포트</div>
                    </div>
                    {chapters_html}
                    <div class="footer">본 리포트는 명리학 기반의 통계적 분석으로, 고객님의 더 나은 내일을 응원합니다.</div>
                </div>
                </body></html>
                """
                
            else:
                saju2 = calculate_saju(birth2, time2)
                prompt = f"""
                고객1: {name1}({gender1}, {saju1}) / 고객2: {name2}({gender2}, {saju2})
                너는 남녀 관계 및 파트너십 분석에 능통한 최고급 컨설턴트야. 두 사람의 궁합을 다루는 8챕터 프리미엄 리포트를 작성해.
                
                [작성 규칙 - 매우 중요]
                각 챕터는 반드시 아래의 마크다운 형식을 정확히 지켜서 출력해.
                ### 챕터명
                > **핵심 요약:** (이곳에 1~2줄로 시선을 끄는 임팩트 있는 요약 작성)
                (이곳에 2~3문단으로 이루어진 깊이 있되 간결한 상세 설명 작성)

                [작성할 8개 챕터 목록]
                1. 운명적 시너지 (두 사람이 만났을 때 폭발하는 긍정적 에너지)
                2. 상호 매력 포인트 (서로가 상대에게 끌릴 수밖에 없는 이유)
                3. 갈등 통제법 (다툼이 발생하기 쉬운 뇌관과 현명한 대처법)
                4. 경제권 주도 (둘 중 누가 돈 관리를 주도해야 재물이 불어나는가)
                5. 함께 그리는 미래 (두 사람이 뭉쳤을 때 달성하기 좋은 목표)
                6. 양가 관계망 (가족 및 주변 사람들과의 원만한 관계 조율법)
                7. 5년 단기 기상도 (향후 5년간 두 사람에게 다가올 중요한 변화)
                8. 파트너십 조언 (완벽한 팀이 되기 위한 핵심 행동 지침)
                """
                raw_text = call_gemini(prompt)
                
                chapters_html = ""
                parts = raw_text.split("###")
                for part in parts:
                    if part.strip():
                        lines = part.strip().split("\n", 1)
                        if len(lines) > 1:
                            title = lines[0].strip()
                            content = markdown.markdown(lines[1].strip())
                            chapters_html += f"<div class='chapter'><h2 class='chapter-title'>{title}</h2><div class='chapter-content'>{content}</div></div>"

                html_export = f"""
                <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="utf-8">{PREMIUM_CSS}</head>
                <body>
                <div class="report-container">
                    <div class="brand-header">
                        <h1>솔 <span>운명상점</span></h1>
                        <p>해처럼 굳건하게, 소나무처럼 푸르게</p>
                        <div class="saju-info">{name1} & {name2} 시너지 리포트</div>
                    </div>
                    {chapters_html}
                    <div class="footer">두 분의 아름다운 인연과 밝은 미래를 진심으로 응원합니다.</div>
                </div>
                </body></html>
                """

            st.success("🎉 생성이 완료되었습니다! 아래 버튼을 눌러 리포트를 저장하거나 바로 확인하세요.")
            
            # 다운로드 버튼
            filename = f"{name1}_개인분석.html" if mode == "👤 개인 분석" else f"{name1}_{name2}_궁합.html"
            st.download_button(label="📥 결과물 스마트폰에 저장하기 (HTML)", data=html_export, file_name=filename, mime="text/html", use_container_width=True)
            
            # 화면에 바로 보여주기 (미리보기)
            st.components.v1.html(html_export, height=800, scrolling=True)