import streamlit as st
from google import genai
from google.genai import types
import datetime, re, math, time, os, base64
import markdown
import streamlit.components.v1 as components

# 📱 프리미엄 모바일 레이아웃 설정
st.set_page_config(page_title="솔 운명상점 Lite Premium V21", layout="centered", initial_sidebar_state="collapsed")
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
        d_str_clean = re.sub(r'\D', '', d_str)
        if len(d_str_clean) == 6:
            yy = int(d_str_clean[:2])
            y = 2000 + yy if yy <= 30 else 1900 + yy
            m = int(d_str_clean[2:4])
            d = int(d_str_clean[4:6])
        elif len(d_str_clean) == 8:
            y = int(d_str_clean[:4])
            m = int(d_str_clean[4:6])
            d = int(d_str_clean[6:8])
        else:
            return None

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
# 🎯 2. 바이럴 루프용 기운 추출기 
# ==========================================
def extract_special_star(text):
    stars_db = {
        "천을귀인": "1", "도화": "3", "괴강": "2", "백호": "4", 
        "홍염": "3", "화개": "5", "역마": "6", "현침": "7",
        "양인": "4", "귀문": "5", "원진": "8"
    }
    for star, percent in stars_db.items():
        if star in text:
            return f"{star}", percent
    return "고유한 귀격", "5"


# ==========================================
# 🎨 3. 고품격 보고서 스타일 CSS (공유 배너 디자인 포함)
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
h3 { display: none; } 

.chapter-content table { width: 100%; border-collapse: collapse; margin: 5px 0 20px 0; font-size: 14.5px; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.03); border: 1px solid #E2E8F0; }
.chapter-content th { background-color: #F8FAFC; color: #0A192F; padding: 14px; text-align: center; font-weight: 800; border-bottom: 2px solid #0A192F; border-right: 1px solid #E2E8F0; }
.chapter-content th:last-child { border-right: none; }
.chapter-content td { padding: 14px; border-bottom: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; text-align: center; color: #333; }
.chapter-content td:last-child { border-right: none; }
.chapter-content tr:last-child td { border-bottom: none; }
.chapter-content tr:hover td { background-color: #F0F4F8; }

.footer { text-align: center; margin-top: 60px; font-size: 12px; color: #CBD5E0; border-top: 1px solid #EDF2F7; padding-top: 25px; }

/* 🌟 하단 공유 배너 CSS (영업용 멘트 + 버튼) */
.share-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #F8FAFC;
    padding: 20px;
    border-radius: 12px;
    margin-top: 40px;
    border: 1px solid #E2E8F0;
    border-left: 5px solid #FEE500;
}
.share-text {
    font-size: 14.5px;
    color: #111;
    font-weight: 600;
    line-height: 1.5;
    flex: 1;
    padding-right: 15px;
}
.share-text span {
    color: #0A192F;
    font-weight: 900;
}
.share-btn {
    background-color: #FEE500;
    color: #000000;
    border: none;
    border-radius: 8px;
    padding: 12px 18px;
    font-size: 14px;
    font-weight: 800;
    cursor: pointer;
    white-space: nowrap;
    font-family: 'Pretendard', sans-serif;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}
.share-btn:hover { background-color: #FDD835; transform: translateY(-2px); }

/* 모바일 화면에서 세로로 자동 정렬되도록 반응형 추가 */
@media (max-width: 480px) {
    .share-banner {
        flex-direction: column;
        text-align: center;
        padding: 20px 15px;
    }
    .share-text {
        padding-right: 0;
        margin-bottom: 15px;
    }
    .share-btn {
        width: 100%;
        padding: 14px;
    }
}
</style>
"""

# ==========================================
# 🚀 4. 메인 앱 UI 및 로직
# ==========================================
st.markdown("<h2 style='text-align: center; color: #0A192F; font-weight: 900;'>솔 운명상점 <span style='color: #D4AF37;'>Lite Premium</span></h2>", unsafe_allow_html=True)

mode = st.radio("분석 모드", ["👤 개인 사주 리포트", "💞 궁합 시너지 리포트"], horizontal=True)

with st.container():
    col1, col2 = st.columns(2)
    with col1: name1 = st.text_input("고객 성함", placeholder="김지훈")
    with col2: gender1 = st.selectbox("성별", ["여성", "남성"])
    
    col3, col4 = st.columns(2)
    with col3: birth1 = st.text_input("생년월일", placeholder="920512 (6자리 또는 8자리)")
    with col4: time1 = st.text_input("태어난 시간", placeholder="0730 (숫자만, 모르면 빈칸)")

if mode == "💞 궁합 시너지 리포트":
    st.markdown("<hr style='border: 0.5px solid #eee;'>", unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5: name2 = st.text_input("상대방 성함", placeholder="김다은")
    with col6: gender2 = st.selectbox("상대방 성별", ["남성", "여성"])
    
    col7, col8 = st.columns(2)
    with col7: birth2 = st.text_input("상대방 생년월일", placeholder="940821 (6자리 또는 8자리)")
    with col8: time2 = st.text_input("상대방 태어난 시간", placeholder="0845 (숫자만, 모르면 빈칸)")

if st.button("🧧 프리미엄 리포트 생성 시작", use_container_width=True):
    if not name1 or not birth1:
        st.warning("필수 정보를 입력해주세요.")
    else:
        with st.spinner("AI 마스터가 심층 데이터 표를 포함한 보고서를 구성 중입니다... (최대 1분 소요)"):
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
                데이터가 드리는 확신과 마음이 전하는 따뜻함으로, {display_name}님의 내일을 함께 설계하겠습니다.<br><br>
                <div style="text-align: right;"><strong>Sol 운명상점 대표 드림</strong></div>
            </div>
            """

            if mode == "👤 개인 사주 리포트":
                prompt = f"""
                고객: {name1} ({gender1}, 명식: {saju_list1})
                너는 '솔 운명상점'의 정통 사주 마스터다. 
                
                [시스템 강제 지침 - 표 깨짐 방지 및 완성도 100% 보장]
                1. 서론/인사말 원천 차단: 절대 인사말을 쓰지 마라.
                2. 호흡 조절: 글이 끊기지 않게 각 서술은 핵심만 밀도 있게 1~2문단 작성.
                3. **[매우 중요] 표와 텍스트 분리:** 모든 파트에서 표(`|---|---|` 형태)를 작성한 직후에는 **반드시 '엔터'를 두 번 쳐서 완벽한 빈 줄을 하나 만든 뒤**에 텍스트 서술을 시작하라. 빈 줄이 없으면 표가 깨진다.
                4. 반드시 9번 파트까지 완벽하게 끝맺어라.

                [출력 템플릿] (아래 양식을 그대로 복사해서 사용하되, 표와 텍스트 사이의 '빈 줄'을 꼭 지켜라)
                
                ### 1. ✨ 타고난 핵심 명식
                | 구분 | 분석 내용 |
                |---|---|
                | 오행 분포 | (🔥화O, 💧수O, 🌳목O, 🪨토O, ⚔️금O) 개수 표기 |
                | 필요 기운 | 내용 |

                (여기에 천간/지지 용어를 활용한 밀도 있는 1~2문단 서술)

                ### 2. 💫 특수 기운과 신살
                | 신살명 | 현대적 해석 |
                |---|---|
                | (신살 나열) | 내용 |

                (여기에 신살이 삶의 무기가 되는 과정을 1~2문단 서술)

                ### 3. 💎 재물운의 그릇
                | 구분 | 핵심 흐름 |
                |---|---|
                | 재물 성향 | 내용 |
                | 발복 시기 | 내용 |

                (여기에 서술 1문단)

                ### 4. 🚀 성공의 자리
                | 구분 | 추천 분야 |
                |---|---|
                | 직무 성향 | 내용 |

                (여기에 서술 1문단)

                ### 5. 🤝 인복과 귀인
                | 구분 | 분석 내용 |
                |---|---|
                | 조심할 인연 | 내용 |

                (여기에 서술 1문단)

                ### 6. 🧘 건강과 활력
                | 구분 | 분석 내용 |
                |---|---|
                | 주의 장기 | 내용 |

                (여기에 서술 1문단)

                ### 7. 🌤️ 2026-2027 운세 기상도
                | 시기 | 핵심 흐름 | 행동 |
                |---|---|---|
                | 26년 하반기 | 내용 | 🔍 관망 |
                | 27년 상반기 | 내용 | 🎯 집중 |

                (여기에 서술 1문단)

                ### 8. 🍀 행운을 부르는 비법
                | 구분 | 행운의 상징 |
                |---|---|
                | 컬러 | 내용 |

                (여기에 서술 1문단)

                ### 9. 💡 마스터의 최종 솔루션
                | 구분 | 실천 지침 |
                |---|---|
                | 행동 지침 | 내용 |

                (여기에 서술 1문단)
                """
                res = client.models.generate_content(model=MODEL_NAME, contents=prompt, config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)).text.strip()
                
            else:
                saju_list2 = calculate_saju(birth2, time2)
                saju_table_html2 = create_saju_table(saju_list2)
                
                prompt = f"""
                고객1: {name1}({gender1}, 명식: {saju_list1}) / 고객2: {name2}({gender2}, 명식: {saju_list2})
                너는 '솔 운명상점'의 정통 궁합 마스터다. 
                
                [시스템 강제 지침 - 표 깨짐 방지 및 완성도 보장]
                1. 서론 금지.
                2. 호흡 조절: 글이 끊기지 않게 각 서술은 핵심만 1~2문단 작성.
                3. **[매우 중요] 표와 텍스트 분리:** 표를 작성한 후 반드시 **빈 줄(엔터)**을 넣고 텍스트를 시작하라.
                4. 반드시 8번 파트까지 완벽히 끝맺어라.

                [출력 템플릿]
                
                ### 1. 🌌 운명적 시너지
                | 구분 | {name1} | {name2} |
                |---|---|---|
                | 총평 | 내용 | 내용 |

                (서술 1~2문단)

                ### 2. 🧩 서로를 채우는 기운
                | 구분 | {name1} | {name2} |
                |---|---|---|
                | 역할 | 내용 | 내용 |

                (서술 1~2문단)

                ### 3. ⚡ 소통과 다툼의 뇌관
                | 구분 | 원인 |
                |---|---|
                | 갈등 | 내용 |

                (서술 1문단)

                ### 4. 💰 경제적 합의 그릇
                | 구분 | 성향 |
                |---|---|
                | 재물 | 내용 |

                (서술 1문단)

                ### 5. 👨‍👩‍👧‍👦 함께 그리는 미래
                | 구분 | 흐름 |
                |---|---|
                | 방향 | 내용 |

                (서술 1문단)

                ### 6. 🏡 가족과의 인연
                | 구분 | 대처법 |
                |---|---|
                | 조언 | 내용 |

                (서술 1문단)

                ### 7. 📈 2026-2027 운세 기상도
                | 시기 | 핵심 흐름 | 행동 |
                |---|---|---|
                | 26년 하반기 | 내용 | 🤝 양보 |
                | 27년 상반기 | 내용 | 🎯 집중 |

                (서술 1문단)

                ### 8. 🤝 완벽한 팀을 위한 약속
                | 구분 | 지침 |
                |---|---|
                | 약속 | 내용 |

                (서술 1문단)
                """
                res = client.models.generate_content(model=MODEL_NAME, contents=prompt, config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)).text.strip()
            
            # --- AI 응답 텍스트에서 강력한 신살 기운 추출 ---
            feature_name, top_percent = extract_special_star(res)

            # HTML 조립
            chapters_html = ""
            parts = res.split("###")
            for p in parts:
                if p.strip():
                    lines = p.strip().split("\n", 1)
                    title = re.sub(r'^[\d\.\s\*#]+', '', lines[0]).strip() 
                    
                    if len(lines) > 1 and title:
                        content = lines[1].strip()
                        # 🚨 [핵심 방어 코드] 표(마지막이 |로 끝나는 줄) 바로 밑에 텍스트가 붙어있으면 강제로 빈 줄을 넣어 표 깨짐을 막음
                        content = re.sub(r'(\|\s*\n)(?!\s*\|)', r'\1\n', content)
                        
                        html_content = markdown.markdown(content, extensions=['tables'])
                        chapters_html += f"""
                        <details>
                            <summary>{title}</summary>
                            <div class='chapter-content'>{html_content}</div>
                        </details>
                        """

            # 🚀 영업용 파이프라인 (카카오톡 오픈채팅방 링크)
            OPEN_CHAT_LINK = "https://open.kakao.com/o/g7frhIri"

            final_html = f"""
            <!DOCTYPE html><html><head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta charset="utf-8">
            {PREMIUM_STYLE_CSS}
            </head>
            <body>
            <div class="report-container">
                {logo_tag}
                <div class="report-header-subtitle">Signature VIP Report</div>
                {greeting_text}
                <div style="margin-bottom:10px; font-weight:800; color:#0A192F; font-size:15px; text-align:center;">[{name1}님의 명식]</div>
                {saju_table_html}
                {f'<div style="margin-bottom:10px; font-weight:800; color:#0A192F; font-size:15px; text-align:center;">[{name2}님의 명식]</div>' + saju_table_html2 if mode == "💞 궁합 시너지 리포트" else ""}
                {chapters_html}
                
                <div class="share-banner">
                    <div class="share-text">
                        ✨ 당신은 상위 <span>{top_percent}%</span>의 <span>{feature_name}</span>을(를) 가진 귀한 분이군요!<br>
                        정말 특별한 명식입니다. 주변에 자랑해보세요 🤫
                    </div>
                    <button class="share-btn" onclick="triggerShare()">
                        💬 공유하기
                    </button>
                </div>

                <div class="footer">솔 운명상점의 VVIP 전용 엔진으로 생성되었습니다.</div>
            </div>

            <script>
                function triggerShare() {{
                    const shareTitle = '🔮 솔 운명상점 VIP 리포트';
                    const shareText = '✨ [솔 운명상점] {name1}님의 명식 분석 결과\\n\\n당신의 사주에서 가장 빛나는 기운은 바로 [ {feature_name} ]! 🌟\\n이는 전체 인구 중 상위 {top_percent}%에게만 허락되는 아주 특별하고 귀한 매력 자본입니다.\\n\\n타고난 그릇과 숨겨진 무기를 제대로 알고 활용하면 인생의 타이밍이 달라집니다.\\n\\n👇 나도 내 운명의 숨겨진 무기가 궁금하다면?\\n👉 내 사주 보러가기: {OPEN_CHAT_LINK}';
                    
                    if (navigator.share) {{
                        navigator.share({{
                            title: shareTitle,
                            text: shareText
                        }}).catch((error) => console.log('공유 취소됨', error));
                    }} else {{
                        alert("아래 텍스트를 복사하여 친구에게 전달해보세요!\\n\\n" + shareText);
                    }}
                }}
            </script>
            </body></html>
            """

            # ==========================================
            # 💡 대표님(관리자)용 앱 화면
            # ==========================================
            st.success("✅ 솔 운명상점 VVIP 리포트 분석이 완료되었습니다! 아래 표들이 정상적으로 출력되었는지 확인 후 다운로드하세요.")
            
            # 관리자용 리포트 다운로드 버튼
            st.download_button(
                label="📥 폰에 리포트 저장하기 (고객 전송용 HTML)", 
                data=final_html, 
                file_name=f"{name1}_솔운명상점_리포트.html", 
                mime="text/html", 
                use_container_width=True
            )

            st.markdown("<br>", unsafe_allow_html=True)
            
            # 화면 하단에 완성된 본문 출력 (미리보기 용)
            st.components.v1.html(final_html, height=1000, scrolling=True)