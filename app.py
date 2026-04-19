import streamlit as st
from google import genai
from google.genai import types
import datetime, re, math, time, os, base64
import markdown

# 📱 프리미엄 모바일 레이아웃 설정
st.set_page_config(page_title="솔 운명상점 Lite Premium V4", layout="centered", initial_sidebar_state="collapsed")
MODEL_NAME = 'gemini-2.5-pro'

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("API 키 설정 오류를 확인해주세요.")
    st.stop()

# ==========================================
# 🖼️ 0. 이미지 HTML 내장 변환 함수
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
        config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)
    )
    return res.text.strip()

# ==========================================
# 🎨 2. 모바일 최적화 프리미엄 스타일 CSS
# ==========================================
PREMIUM_STYLE_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
body { background-color: #f4f4f5; margin: 0; padding: 0; color: #111; line-height: 1.7; word-break: keep-all; }

.report-container { max-width: 800px; margin: 0 auto; background-color: #FFFFFF; padding: 40px 15px; border-radius: 0; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-top: 10px solid #0A192F; }

/* 📱 휴대폰 화면에서 로고가 꽉 차게 조절 */
.logo-box { text-align: center; margin-bottom: 35px; width: 100%; }
.logo-box img { width: 100%; max-width: 600px; height: auto; display: block; margin: 0 auto; }

.report-header-subtitle { text-align: center; font-size: 13px; color: #D4AF37; font-weight: 700; letter-spacing: 3px; margin-bottom: 40px; text-transform: uppercase; border-bottom: 1px solid #eee; padding-bottom: 15px; }

/* 고정 인사말 박스 */
.greeting-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 25px; border-radius: 12px; margin-bottom: 35px; border-left: 6px solid #0A192F; line-height: 1.8; font-size: 15px; color: #333; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
.greeting-box strong { color: #0A192F; font-size: 16px; font-weight: 800; }

/* 명식 선언 박스 */
.saju-declaration { background-color: #0A192F; color: #D4AF37; padding: 20px; border-radius: 8px; font-weight: 700; text-align: center; margin-bottom: 40px; font-size: 15px; letter-spacing: 1px; }

/* 챕터 디자인 */
.chapter-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0A192F; padding-bottom: 10px; margin-top: 60px; margin-bottom: 25px; }
.chapter-title { font-size: 20px; font-weight: 900; color: #0A192F; }
.methodology { font-size: 11px; color: #A0AEC0; font-weight: 600; }

/* 형광펜 요약 박스 */
blockquote { background-color: #FFFBEB; border-left: 6px solid #D4AF37; padding: 20px; margin: 0 0 30px 0; border-radius: 6px; font-weight: 700; color: #111; font-size: 16px; line-height: 1.6; box-shadow: 0 2px 4px rgba(212, 175, 55, 0.1); }
blockquote p { margin: 0; }

/* 상세 분석 텍스트 */
h3 { display: none; }
.detail-content { font-size: 15.5px; color: #333; text-align: justify; margin-bottom: 40px; padding: 0 5px; }
strong { color: #800020; font-weight: 900; }

.footer { text-align: center; margin-top: 70px; font-size: 12px; color: #CBD5E0; border-top: 1px solid #EDF2F7; padding-top: 25px; letter-spacing: 1px; }
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
        with st.spinner("AI 마스터가 8~9개 파트의 정밀 분석을 수행 중입니다..."):
            saju_val1 = calculate_saju(birth1, time1)
            
            # [이미지 처리] 로컬의 PNG 파일을 읽어서 HTML에 내장 (Base64)
            img_base64 = get_base64_image("sol운명상점.png")
            if img_base64:
                logo_img_tag = f"<div class='logo-box'><img src='{img_base64}' alt='솔 운명상점 로고'></div>"
            else:
                logo_img_tag = f"<div class='logo-box'><h1 style='color:#0A192F; margin:0;'>SOL</h1><div style='color:#D4AF37; font-weight:bold; letter-spacing:3px;'>운명상점</div></div>"
            
            # [고정 인사말]
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
                # 8~9개 파트 강제 지시 (찐최종사주.txt 기반)
                prompt = f"""
                고객: {name1} ({gender1}, 명식: {saju_val1})
                너는 '솔 운명상점'의 시그니처 VIP 리포트를 작성하는 마스터다. 
                아래 명시된 9개 장(Chapter)을 한 줄도 빠짐없이, 고품격 평문으로 상세히 작성하라. 
                분량은 라이트하지만 깊이가 느껴져야 하며, 번호 매기기나 기계적인 리스트는 절대 사용하지 마라.

                [필수 구성 9챕터]
                1. 코어 에너지 (타고난 본성과 기본 기질)
                2. 성격의 명암 (강점과 치명적 약점 보완책)
                3. 재물운의 그릇 (부의 흐름과 돈을 모으는 타이밍)
                4. 성공의 포지션 (직장/사업에서 가장 빛나는 역할)
                5. 인복과 귀인 (인간관계에서 득이 되는 사람과 독이 되는 사람)
                6. 애정운의 향방 (나를 완성해줄 파트너의 조건)
                7. 헬스케어 가이드 (주의해야 할 장기와 활력 유지법)
                8. 2026-2027 전술 기상도 (향후 2년의 거시적 운세 흐름)
                9. 마스터의 최종 솔루션 (내일 당장 운을 깨우는 행동 지침)

                [작성 형식]
                각 장은 반드시 아래 형식을 지켜라:
                ### 제 N장. 제목
                > **핵심 요약:** (1~2줄의 임팩트 있는 핵심 키워드 요약)
                **[상세 분석]**
                (이곳에 2~3문단의 풍성하고 부드러운 평문 서술)
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
                    <div class="report-header-subtitle">Premium Destiny Analysis Solution</div>
                    {greeting_html}
                    <div class="saju-declaration">{name1}님의 명식: {saju_val1}</div>
                    {chapters_html}
                    <div class="footer">본 리포트는 솔 운명상점의 VVIP 전용 엔진으로 생성되었습니다.</div>
                </div>
                </body></html>
                """

            else:
                saju_val2 = calculate_saju(birth2, time2)
                prompt = f"""
                고객1: {name1}({gender1}, {saju_val1}) / 고객2: {name2}({gender2}, {saju_val2})
                너는 두 사람의 인연을 분석하는 '솔 운명상점'의 시그니처 궁합 마스터다. 
                아래 8개 챕터를 반드시 포함하여 품격 있는 평문으로 리포트를 완성하라.

                [필수 구성 8챕터]
                1. 운명적 시너지 (두 사람 결합의 전체적인 총평)
                2. 상호 보완의 에너지 (서로의 부족함을 어떻게 채워주는가)
                3. 소통과 갈등의 뇌관 (다툼의 원인과 현명한 대처 지침)
                4. 경제적 합의 그릇 (누가 재권을 쥐어야 부유해지는가)
                5. 함께 그리는 미래 (두 사람이 만났을 때 생기는 사회적 운)
                6. 시가/처가와의 유기성 (가족 관계에서 주의할 스탠스)
                7. 5년 단기 기상도 (향후 5년 내 가장 주의할 점과 기회)
                8. 파트너십 개운법 (완벽한 팀이 되기 위한 내일의 실천)

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
                    <div class="report-header-subtitle">Premium Partnership Harmony Solution</div>
                    {greeting_html}
                    <div class="saju-declaration">{name1}({saju_val1}) & {name2}({saju_val2})</div>
                    {chapters_html}
                    <div class="footer">두 분의 밝은 인연과 행복한 미래를 솔 운명상점이 기원합니다.</div>
                </div>
                </body></html>
                """

            st.success("✅ 고품격 프리미엄 리포트가 완성되었습니다!")
            st.download_button("📥 스마트폰에 리포트 저장하기", data=final_html, file_name=f"{name1}_리포트.html", mime="text/html", use_container_width=True)
            st.components.v1.html(final_html, height=1000, scrolling=True)