import streamlit as st
from google import genai
from google.genai import types
import datetime, re, math, time, os, base64
import markdown

# 📱 프리미엄 모바일 레이아웃 설정 (딥 네이비 & 웜 골드)
st.set_page_config(page_title="솔 운명상점 Lite Premium V3", layout="centered", initial_sidebar_state="collapsed")
MODEL_NAME = 'gemini-2.5-pro'

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("API 키 설정 오류를 확인해주세요.")
    st.stop()

# ==========================================
# 🖼️ 0. 이미지 HTML 내장 변환 함수 (카톡 전송 시 깨짐 방지)
# ==========================================
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    return None

# ==========================================
# ⚙️ 1. 사주 명식 계산 엔진
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
        return f"{yp}, {mp}, {dp_str}, {hp}"
    except: return None

def call_gemini(prompt):
    res = client.models.generate_content(
        model=MODEL_NAME, 
        contents=prompt, 
        config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=4096)
    )
    return res.text.strip()

# ==========================================
# 🎨 2. 김지훈/김다은 스타일 프리미엄 CSS
# ==========================================
PREMIUM_STYLE_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
body { background-color: #f4f4f5; margin: 0; padding: 10px; color: #111; line-height: 1.7; word-break: keep-all; }

.report-container { max-width: 800px; margin: 0 auto; background-color: #FFFFFF; padding: 40px 20px; border-radius: 0; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-top: 8px solid #0A192F; }

/* 엠블럼/로고 이미지 영역 */
.logo-box { text-align: center; margin-bottom: 25px; }
.logo-box img { max-width: 250px; height: auto; }

.report-header-title { text-align: center; font-size: 26px; font-weight: 900; color: #0A192F; margin-bottom: 10px; }
.report-header-subtitle { text-align: center; font-size: 14px; color: #D4AF37; font-weight: 700; letter-spacing: 2px; margin-bottom: 30px; text-transform: uppercase; }

/* 대표님 고정 인사말 박스 */
.greeting-box { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 25px; border-radius: 8px; margin-bottom: 30px; border-left: 4px solid #0A192F; line-height: 1.8; font-size: 15px; color: #333; }
.greeting-box strong { color: #0A192F; font-size: 16px; }

/* 명식 선언 박스 */
.saju-declaration { background-color: #F8FAFC; border: 1px solid #E2E8F0; color: #2D3748; padding: 20px; border-radius: 8px; font-weight: 700; text-align: center; margin-bottom: 40px; font-size: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }

/* 챕터 타이틀 */
.chapter-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0A192F; padding-bottom: 8px; margin-top: 50px; margin-bottom: 20px; }
.chapter-title { font-size: 19px; font-weight: 900; color: #0A192F; }
.methodology { font-size: 11px; color: #A0AEC0; font-weight: 600; }

/* 형광펜 요약 박스 */
blockquote { background-color: #FFFBEB; border-left: 5px solid #D4AF37; padding: 18px; margin: 0 0 25px 0; border-radius: 4px; font-weight: 700; color: #111; font-size: 15.5px; line-height: 1.6; }
blockquote p { margin: 0; }

/* 상세 분석 텍스트 */
h3 { display: none; }
.detail-content { font-size: 15px; color: #333; text-align: justify; margin-bottom: 30px; padding-left: 2px; }
strong { color: #800020; font-weight: 800; }

.footer { text-align: center; margin-top: 50px; font-size: 12px; color: #CBD5E0; border-top: 1px solid #EDF2F7; padding-top: 20px; }
</style>
"""

# ==========================================
# 🚀 3. 메인 앱 UI
# ==========================================
st.markdown("<h2 style='text-align: center; color: #0A192F; font-weight: 900;'>솔 운명상점 <span style='color: #D4AF37;'>Lite Premium</span></h2>", unsafe_allow_html=True)

mode = st.radio("분석 모드", ["👤 개인 사주 리포트", "💞 궁합 시너지 리포트"], horizontal=True)

with st.container():
    col1, col2 = st.columns(2)
    with col1: name1 = st.text_input("고객 성함", placeholder="김지훈")
    with col2: gender1 = st.selectbox("성별", ["여성", "남성"])
    
    col3, col4 = st.columns(2)
    with col3: birth1 = st.text_input("생년월일 (8자리)", placeholder="19920512")
    with col4: time1 = st.text_input("태어난 시간", placeholder="07:30 (모르면 비워두기)")

if mode == "💞 궁합 시너지 리포트":
    st.markdown("<hr style='border: 0.5px solid #eee;'>", unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5: name2 = st.text_input("상대방 성함", placeholder="김다은")
    with col6: gender2 = st.selectbox("상대방 성별", ["남성", "여성"])
    
    col7, col8 = st.columns(2)
    with col7: birth2 = st.text_input("상대방 생년월일", placeholder="19940821")
    with col8: time2 = st.text_input("상대방 태어난 시간", placeholder="모르면 비워두기")

if st.button("🧧 프리미엄 리포트 생성 시작", use_container_width=True):
    if not name1 or not birth1:
        st.warning("성함과 생년월일은 필수 입력 항목입니다.")
    else:
        with st.spinner("AI 마스터가 명식을 분석 중입니다..."):
            saju_val1 = calculate_saju(birth1, time1)
            
            # [이미지 처리] 로컬의 PNG 파일을 읽어서 HTML에 내장시킵니다.
            img_base64 = get_base64_image("sol운명상점.png")
            if img_base64:
                logo_img_tag = f"<div class='logo-box'><img src='{img_base64}' alt='솔 운명상점 로고'></div>"
            else:
                logo_img_tag = f"<div class='logo-box'><h1 style='color:#0A192F; margin:0;'>SOL</h1><div style='color:#D4AF37; font-weight:bold; letter-spacing:3px;'>운명상점</div></div>"
            
            # [고정 인사말 생성] 궁합일 경우 두 사람 이름을 모두 표기합니다.
            display_name = f"{name1}님, {name2}" if mode == "💞 궁합 시너지 리포트" and name2 else name1
            greeting_html = f"""
            <div class="greeting-box">
                <strong>안녕하세요, {display_name}님.</strong><br><br>
                저희 Sol 운명상점을 이용해 주셔서 진심으로 감사합니다.<br>
                Sol 운명상점은 고전 명리학의 지혜와 MBTI를 결합한 운명 분석 전문 기업입니다.<br>
                저희 브랜드 네임인 'Sol'에는 Solar(앞길을 비추는 태양)와 Solution(실질적인 해답)의 가치가 담겨 있습니다.<br>
                데이터가 드리는 확신과 마음이 전하는 따뜻함으로, {display_name}님의 내일을 함께 설계하겠습니다.<br><br>
                <div style="text-align: right;"><strong>Sol 운명상점 대표 드림</strong></div>
            </div>
            """

            if mode == "👤 개인 사주 리포트":
                prompt = f"""
                고객: {name1} ({gender1}, 명식: {saju_val1})
                너는 '김지훈_VIP솔루션' 스타일의 고품격 사주 리포트를 작성하는 마스터다. 
                내용은 명료하게 줄이되, 구성은 반드시 아래 8개 장(Chapter)을 모두 포함해야 한다. 
                문체는 정중하고 자연스러운 평문(해요체/하십시오체)을 사용하고, 기계적인 느낌의 번호 매기기나 과도한 이모티콘을 빼라.

                [필수 구성 8챕터]
                1. 코어 에너지 (본성과 기질)
                2. 재물운의 그릇 (부의 흐름과 타이밍)
                3. 직업적 성공 지점 (최적의 사회적 포지션)
                4. 인복과 귀인 (나를 돕는 사람과 경계할 사람)
                5. 헬스케어 가이드 (주의할 장기와 활력 유지법)
                6. 2026-2027 기상도 (향후 2년의 핵심 운세)
                7. 공간 개운법 (행운을 부르는 방위와 인테리어)
                8. 마스터의 최종 조언 (내일 당장 실천할 운명 개선책)

                [작성 형식]
                각 장은 반드시 아래 형식을 지켜라:
                ### 제 N장. 제목
                > **핵심 요약:** (이곳에 1~2줄로 임팩트 있는 요약 작성)
                **[상세 분석]**
                (이곳에 2~3문단으로 상세 설명 기술)
                """
                raw_res = call_gemini(prompt)
                
                chapters_html = ""
                parts = raw_res.split("###")
                for p in parts:
                    if p.strip():
                        lines = p.strip().split("\n", 1)
                        title = lines[0].replace("제 ", "").strip()
                        content = markdown.markdown(lines[1].strip()) if len(lines) > 1 else ""
                        chapters_html += f"""
                        <div class='chapter-header'>
                            <div class='chapter-title'>{title}</div>
                            <div class='methodology'>※ 자평명리/심리학 융합 분석</div>
                        </div>
                        <div class='chapter-content'>{content}</div>
                        """
                
                final_html = f"""
                <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="utf-8">{PREMIUM_STYLE_CSS}</head>
                <body>
                <div class="report-container">
                    {logo_img_tag}
                    <div class="report-header-title">[{name1}님] VIP 솔루션 리포트</div>
                    <div class="report-header-subtitle">Premium Destiny Analysis</div>
                    {greeting_html}
                    <div class="saju-declaration">{name1}님의 명식은 {saju_val1} 입니다.</div>
                    {chapters_html}
                    <div class="footer">본 리포트는 솔 운명상점의 VVIP 전용 엔진으로 생성되었습니다.</div>
                </div>
                </body></html>
                """

            else:
                saju_val2 = calculate_saju(birth2, time2)
                prompt = f"""
                고객1: {name1}({gender1}, {saju_val1}) / 고객2: {name2}({gender2}, {saju_val2})
                너는 '김다은_김지훈_프리미엄_궁합' 스타일의 시너지 리포트를 작성하는 마스터다. 
                아래 8개 챕터를 반드시 포함하여 두 사람의 인연을 깊이 있게 분석하라.
                문체는 정중하고 자연스러운 평문을 사용하라.

                [필수 구성 8챕터]
                1. 운명적 시너지 (두 사람 결합의 총평)
                2. 상호 보완점 (서로가 서로에게 채워주는 에너지)
                3. 소통과 다툼의 뇌관 (갈등의 원인과 예방법)
                4. 경제적 합 (누가 돈을 관리해야 하는가)
                5. 자녀 및 가족운 (가정을 꾸렸을 때의 흐름)
                6. 시가/처가와의 합 (주변 인간관계 스탠스)
                7. 향후 5년 파트너십 기상도 (비즈니스/연애 흐름)
                8. 완벽한 팀을 위한 조언 (서로를 위한 약속)

                [작성 형식 동일]
                """
                raw_res = call_gemini(prompt)
                
                chapters_html = ""
                parts = raw_res.split("###")
                for p in parts:
                    if p.strip():
                        lines = p.strip().split("\n", 1)
                        title = lines[0].strip()
                        content = markdown.markdown(lines[1].strip()) if len(lines) > 1 else ""
                        chapters_html += f"""
                        <div class='chapter-header'>
                            <div class='chapter-title'>{title}</div>
                            <div class='methodology'>※ 명리 조후 및 합충 분석</div>
                        </div>
                        <div class='chapter-content'>{content}</div>
                        """

                final_html = f"""
                <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="utf-8">{PREMIUM_STYLE_CSS}</head>
                <body>
                <div class="report-container">
                    {logo_img_tag}
                    <div class="report-header-title">[{name1} & {name2}] 시너지 리포트</div>
                    <div class="report-header-subtitle">Premium Partnership Harmony</div>
                    {greeting_html}
                    <div class="saju-declaration">{name1}({saju_val1})님과 {name2}({saju_val2})님의 결합 분석입니다.</div>
                    {chapters_html}
                    <div class="footer">두 분의 앞날에 밝은 기운이 가득하기를 솔 운명상점이 기원합니다.</div>
                </div>
                </body></html>
                """

            st.success("✅ 프리미엄 리포트가 완성되었습니다!")
            st.download_button("📥 스마트폰에 리포트 저장하기", data=final_html, file_name=f"{name1}_리포트.html", mime="text/html", use_container_width=True)
            st.components.v1.html(final_html, height=1000, scrolling=True)