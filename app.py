import streamlit as st
from google import genai
from google.genai import types
import datetime, re, math, time, os, base64
import markdown

# 📱 프리미엄 모바일 레이아웃 설정
st.set_page_config(page_title="솔 운명상점 Lite Premium V6", layout="centered", initial_sidebar_state="collapsed")
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
# ⚙️ 1. 사주 명식 계산 및 표 변환 엔진
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
        
        # 📱 휴대폰 입력 편의성을 위한 시간 자동 파싱 (0743 -> 07시 43분)
        t_str_clean = re.sub(r'\D', '', t_str)
        if len(t_str_clean) >= 3:
            hr = int(t_str_clean[:-2])
            mn = int(t_str_clean[-2:])
        elif len(t_str_clean) > 0:
            hr = int(t_str_clean)
            mn = 0
        else:
            hr, mn = 0, 0

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
        return [yp, mp, dp_str, hp] 
    except: return None

def create_saju_table(saju_list):
    if not saju_list: return ""
    titles = ["시주(時)", "일주(日)", "월주(月)", "연주(年)"]
    data = saju_list[::-1] 
    
    html = "<table class='saju-table'><tr>"
    for t in titles: html += f"<th>{t}</th>"
    html += "</tr><tr>"
    for d in data: html += f"<td>{d[0]}</td>" 
    html += "</tr><tr>"
    for d in data: html += f"<td>{d[1]}</td>" 
    html += "</tr></table>"
    return html

# ==========================================
# 🎨 2. 고품격 보고서 스타일 CSS
# ==========================================
PREMIUM_STYLE_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
body { background-color: #f4f4f5; margin: 0; padding: 0; color: #111; line-height: 1.7; word-break: keep-all; }

.report-container { max-width: 800px; margin: 0 auto; background-color: #FFFFFF; padding: 40px 15px; border-top: 12px solid #0A192F; }

.logo-box { text-align: center; margin-bottom: 30px; width: 100%; }
.logo-box img { width: 100%; max-width: 600px; height: auto; display: block; margin: 0 auto; }

.report-header-subtitle { text-align: center; font-size: 13px; color: #D4AF37; font-weight: 700; letter-spacing: 3px; margin-bottom: 35px; text-transform: uppercase; border-bottom: 1px solid #eee; padding-bottom: 15px; }

.greeting-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 25px; border-radius: 12px; margin-bottom: 35px; border-left: 6px solid #0A192F; font-size: 15px; }
.greeting-box strong { color: #0A192F; font-size: 16px; }

.saju-table { width: 100%; border-collapse: collapse; margin-bottom: 40px; text-align: center; table-layout: fixed; border: 2px solid #0A192F; }
.saju-table th { background-color: #0A192F; color: #D4AF37; padding: 10px; font-size: 14px; border: 1px solid #2D3748; }
.saju-table td { padding: 15px 5px; border: 1px solid #E2E8F0; font-size: 20px; font-weight: 900; color: #111; background-color: #fff; }

details { margin-bottom: 15px; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; transition: all 0.3s ease; }
summary { padding: 18px 20px; background-color: #F8FAFC; color: #0A192F; font-size: 17px; font-weight: 800; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid transparent; }
summary::-webkit-details-marker { display: none; }
summary::after { content: '▼'; font-size: 12px; color: #D4AF37; }
details[open] { border: 1px solid #0A192F; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
details[open] summary { background-color: #0A192F; color: #D4AF37; border-bottom: 1px solid #0A192F; }
details[open] summary::after { content: '▲'; }

.chapter-content { padding: 25px; font-size: 15.5px; color: #333; background-color: #fff; }
blockquote { background-color: #FFFBEB; border-left: 6px solid #D4AF37; padding: 15px; margin: 0 0 20px 0; border-radius: 4px; font-weight: 700; color: #111; }
h3 { display: none; }

/* 🌟 본문 내 AI 생성 표(Table) 프리미엄 스타일링 */
.chapter-content table { width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 14px; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.03); border: 1px solid #E2E8F0; }
.chapter-content th { background-color: #F8FAFC; color: #0A192F; padding: 14px; text-align: center; font-weight: 800; border-bottom: 2px solid #0A192F; border-right: 1px solid #E2E8F0; }
.chapter-content th:last-child { border-right: none; }
.chapter-content td { padding: 14px; border-bottom: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; text-align: center; color: #333; }
.chapter-content td:last-child { border-right: none; }
.chapter-content tr:last-child td { border-bottom: none; }
.chapter-content tr:hover td { background-color: #F0F4F8; }

.footer { text-align: center; margin-top: 60px; font-size: 12px; color: #CBD5E0; border-top: 1px solid #EDF2F7; padding-top: 25px; }
</style>
"""

# ==========================================
# 🚀 3. 메인 앱 UI 및 로직
# ==========================================
st.markdown("<h2 style='text-align: center; color: #0A192F; font-weight: 900;'>솔 운명상점 <span style='color: #D4AF37;'>Lite Premium</span></h2>", unsafe_allow_html=True)

mode = st.radio("분석 모드", ["👤 개인 사주 리포트", "💞 궁합 시너지 리포트"], horizontal=True)

with st.container():
    col1, col2 = st.columns(2)
    with col1: name1 = st.text_input("고객 성함", placeholder="김지훈")
    with col2: gender1 = st.selectbox("성별", ["여성", "남성"])
    
    col3, col4 = st.columns(2)
    with col3: birth1 = st.text_input("생년월일 (8자리)", placeholder="19920512")
    with col4: time1 = st.text_input("태어난 시간", placeholder="0730 (기호 없이 숫자만)")

if mode == "💞 궁합 시너지 리포트":
    st.markdown("<hr style='border: 0.5px solid #eee;'>", unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5: name2 = st.text_input("상대방 성함", placeholder="김다은")
    with col6: gender2 = st.selectbox("상대방 성별", ["남성", "여성"])
    
    col7, col8 = st.columns(2)
    with col7: birth2 = st.text_input("상대방 생년월일", placeholder="19940821")
    with col8: time2 = st.text_input("상대방 태어난 시간", placeholder="0845 (기호 없이 숫자만)")

if st.button("🧧 프리미엄 리포트 생성 시작", use_container_width=True):
    if not name1 or not birth1:
        st.warning("정보를 입력해주세요.")
    else:
        with st.spinner("AI 마스터가 심층 데이터 표를 포함한 보고서를 구성 중입니다..."):
            saju_list1 = calculate_saju(birth1, time1) 
            saju_table_html = create_saju_table(saju_list1)
            
            img_base64 = get_base64_image("sol운명상점.png")
            logo_tag = f"<div class='logo-box'><img src='{img_base64}'></div>" if img_base64 else ""
            
            display_name = f"{name1}님, {name2}" if mode == "💞 궁합 시너지 리포트" and name2 else name1
            greeting_text = f"""
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
                고객: {name1} ({gender1}, 명식: {saju_list1})
                너는 '솔 운명상점'의 마스터다. 인사말이나 서론 없이 바로 결과만 출력하라.
                
                [작성 핵심 지침]
                1. 상단의 요약(>)은 구구절절 설명하지 말고 **10자 내외의 핵심 키워드**로 극도로 압축하라.
                2. 상세 분석 본문은 기존보다 살을 덧붙여서 **각 파트당 3~4문단의 깊이 있는 평문**으로 서술하라.
                3. 프리미엄 보고서 느낌을 주기 위해, **최소 3개 이상의 파트(예: 성격의 명암, 직업운, 26-27년 운세 등)에는 반드시 마크다운 표(Markdown Table)를 삽입**하여 핵심 데이터를 시각화하라. 표의 내용은 창의적이고 전문적으로 구성하라.

                [필수 구성 9파트]
                1. ✨ 코어 에너지 (기본 기질)
                2. 🌗 성격의 명암 (강점과 약점을 표로 비교)
                3. 💎 재물운의 그릇 (부의 타이밍)
                4. 🚀 성공의 포지션 (직업운 분석표 포함)
                5. 🤝 인복과 귀인 (인간관계)
                6. 🧘 헬스케어 가이드 (건강)
                7. 🌤️ 2026-2027 전술 기상도 (연도별 운세 흐름을 표로 정리)
                8. 🍀 행운의 개운법 (방위/컬러)
                9. 💡 마스터의 최종 솔루션

                [출력 형식]
                ### 파트제목
                > **요약:** 10자 내외 단답형 키워드
                본문내용 (3~4문단 상세 설명)
                
                | 항목 | 설명 | (필요한 곳에 마크다운 표 삽입)
                |---|---|
                | 데이터 | 데이터 |
                """
                res = client.models.generate_content(model=MODEL_NAME, contents=prompt, config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)).text.strip()
                
                chapters_html = ""
                parts = res.split("###")
                for p in parts:
                    if p.strip():
                        lines = p.strip().split("\n", 1)
                        title = lines[0].strip()
                        # markdown의 tables 확장을 사용하여 표를 HTML로 자동 변환
                        content = markdown.markdown(lines[1].strip(), extensions=['tables']) if len(lines) > 1 else ""
                        chapters_html += f"""
                        <details>
                            <summary>{title}</summary>
                            <div class='chapter-content'>{content}</div>
                        </details>
                        """

                final_html = f"""
                <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="utf-8">{PREMIUM_STYLE_CSS}</head>
                <body>
                <div class="report-container">
                    {logo_tag}
                    <div class="report-header-subtitle">Signature VIP Destiny Report</div>
                    {greeting_text}
                    <div style="margin-bottom:10px; font-weight:800; color:#0A192F; font-size:15px; letter-spacing:1px; text-align:center;">[{name1}님의 사주 명식]</div>
                    {saju_table_html}
                    {chapters_html}
                    <div class="footer">본 리포트는 솔 운명상점의 VVIP 전용 엔진으로 생성되었습니다.</div>
                </div>
                </body></html>
                """

            else:
                saju_list2 = calculate_saju(birth2, time2)
                saju_table_html2 = create_saju_table(saju_list2)
                
                prompt = f"""
                고객1: {name1}({gender1}, 명식: {saju_list1}) / 고객2: {name2}({gender2}, 명식: {saju_list2})
                너는 '솔 운명상점'의 궁합 마스터다. 인사말 없이 바로 결과를 출력하라.
                
                [작성 핵심 지침]
                1. 요약(>)은 **10자 내외 핵심 키워드**로 압축.
                2. 본문은 **3~4문단의 깊이 있는 평문**으로 서술.
                3. **최소 3개 이상의 파트(예: 보완점, 경제적 합, 5년 운세 등)에 반드시 마크다운 표(Table)를 삽입**하여 두 사람의 시너지를 고급스럽게 시각화할 것.

                [필수 구성 8파트]
                1. 🌌 운명적 시너지 (총평)
                2. 🧩 상호 보완의 에너지 (두 사람의 시너지 표 포함)
                3. ⚡ 소통과 갈등의 뇌관 (다툼 예방)
                4. 💰 경제적 합의 그릇 (재물 관리 성향 비교표 포함)
                5. 👨‍👩‍👧‍👦 함께 그리는 미래 (가족/자녀)
                6. 🏡 시가/처가와의 유기성 (가족관계)
                7. 📈 향후 3년 단기 기상도 (연도별 궁합 흐름 표 포함)
                8. 🤝 파트너십 개운법 (행동지침)
                """
                res = client.models.generate_content(model=MODEL_NAME, contents=prompt, config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)).text.strip()
                
                chapters_html = ""
                parts = res.split("###")
                for p in parts:
                    if p.strip():
                        lines = p.strip().split("\n", 1)
                        title = lines[0].strip()
                        content = markdown.markdown(lines[1].strip(), extensions=['tables']) if len(lines) > 1 else ""
                        chapters_html += f"""
                        <details>
                            <summary>{title}</summary>
                            <div class='chapter-content'>{content}</div>
                        </details>
                        """

                final_html = f"""
                <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="utf-8">{PREMIUM_STYLE_CSS}</head>
                <body>
                <div class="report-container">
                    {logo_tag}
                    <div class="report-header-subtitle">Signature VIP Harmony Report</div>
                    {greeting_text}
                    
                    <div style="margin-bottom:10px; font-weight:800; color:#0A192F; font-size:14px; text-align:center;">[{name1}님의 명식]</div>
                    {saju_table_html}
                    <div style="margin-bottom:10px; font-weight:800; color:#0A192F; font-size:14px; text-align:center;">[{name2}님의 명식]</div>
                    {saju_table_html2}
                    
                    {chapters_html}
                    <div class="footer">두 분의 밝은 인연과 행복한 미래를 솔 운명상점이 기원합니다.</div>
                </div>
                </body></html>
                """

            st.success("✅ 고품격 데이터 표가 포함된 리포트가 완성되었습니다!")
            st.download_button("📥 리포트 다운로드 (HTML)", data=final_html, file_name=f"{name1}_솔운명상점_리포트.html", mime="text/html", use_container_width=True)
            st.components.v1.html(final_html, height=1200, scrolling=True)