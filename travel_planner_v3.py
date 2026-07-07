import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import base64

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="여행 플래너 ✈️", page_icon="✈️", layout="wide")

# ✨ CSS: 오직 이모티콘 버튼들의 박스만 정밀하게 날려버리고 여백을 조절하는 특수 스타일 적용
st.markdown("""
    <style>
    /* .icon-btn-wrapper 라는 숨겨진 마커 바로 옆에 생성된 버튼만 테두리/배경 투명화 */
    div[data-testid="stMarkdownContainer"]:has(.icon-btn-wrapper) + div[data-testid="stButton"] > button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0px !important;
        margin: 0px !important;
        height: auto !important;
        min-height: unset !important;
        font-size: 20px !important;
        color: #555 !important;
    }
    div[data-testid="stMarkdownContainer"]:has(.icon-btn-wrapper) + div[data-testid="stButton"] > button:hover {
        color: #ff4b4b !important;
        background-color: transparent !important;
    }
    
    /* 상단 저장 버튼 등 원래 유지해야 하는 일반/기본 버튼 보호 */
    div.stButton > button[data-testid="baseButton-primary"] {
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* 📌 일정 사이의 간격을 대폭 줄이고 정렬하기 위한 스타일 */
    .schedule-container {
        background-color: #FFFFFF; 
        padding: 10px 14px; 
        border-radius: 8px; 
        border-left: 5px solid #ff4b4b; 
        margin-bottom: 0px; 
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    .arrow-container {
        text-align: center;
        margin: -4px 0 -4px 0;
        line-height: 1;
    }
    </style>
""", unsafe_allow_html=True)

# 박스 없는 이모티콘 버튼을 만들어주는 헬퍼 함수
def icon_button(label, key, help_text):
    st.markdown('<div class="icon-btn-wrapper" style="display:none;"></div>', unsafe_allow_html=True)
    try:
        return st.button(label, key=key, help=help_text, type="tertiary")
    except:
        return st.button(label, key=key, help=help_text)

# 🌐 파이어베이스 실시간 DB 주소
FIREBASE_URL = "https://my-planner-fc3a5-default-rtdb.firebaseio.com/"

# --- 🌐 파이어베이스 통신용 함수 ---
@st.cache_data(show_spinner=False, ttl=1)
def db_load_cached(path):
    try:
        url = f"{FIREBASE_URL}{path}.json"
        response = requests.get(url)
        if response.status_code == 200 and response.text != "null":
            return response.json()
    except:
        pass
    return None

def db_load(path):
    return db_load_cached(path)

def db_save(path, data):
    try:
        url = f"{FIREBASE_URL}{path}.json"
        response = requests.put(url, json=data)
        st.cache_data.clear()
        return response.status_code == 200
    except:
        return False

def encode_image(file):
    if file is not None:
        return base64.b64encode(file.getvalue()).decode()
    return None

# 디폴트 빈 플래너 생성 함수
def get_default_trip():
    return {
        "trip_title": "나의 특별한 여행",
        "start_date": datetime.today().strftime("%Y-%m-%d"),
        "itinerary": {
            "Day 1": {
                "schedule": [], "image_base64": None, "notes": "", "meals": {"아침": "", "점심": "", "저녁": ""}
            }
        }
    }

# 2. 로컬 세션 상태 관리 초기화
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = "로그인"
if 'page_view' not in st.session_state: st.session_state.page_view = "🏠 홈 (플래너 짜기)"

# --- 🔐 인증 시스템 화면 ---
def show_auth_page():
    st.markdown("<h2 style='text-align: center; margin-bottom: 25px;'>여행 플래너 ✈️</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        if st.session_state.auth_mode == "로그인":
            st.markdown("### 🔐 로그인")
            with st.form(key="login_form"):
                login_id = st.text_input("아이디(ID)", placeholder="아이디 입력").strip()
                login_pw = st.text_input("비밀번호(Password)", type="password", placeholder="비밀번호 입력").strip()
                submit_login = st.form_submit_button("로그인하기", use_container_width=True)
                
                if submit_login:
                    if not login_id or not login_pw:
                        st.error("❌ 아이디와 비밀번호를 모두 입력해 주세요.")
                    else:
                        saved_pw = db_load(f"users/{login_id}")
                        if saved_pw and saved_pw == login_pw:
                            st.session_state.logged_in = True
                            st.session_state.current_user = login_id
                            st.success(f"🎉 {login_id}님, 로그인 성공!")
                            st.rerun()
                        else:
                            st.error("❌ 아이디 또는 비밀번호가 일치하지 않습니다.")
            
            st.caption("아직 계정이 없으신가요?")
            if st.button("📝 새로운 회원가입 하러가기", use_container_width=True):
                st.session_state.auth_mode = "회원가입"
                st.rerun()
                        
        elif st.session_state.auth_mode == "회원가입":
            st.markdown("### 📝 새로운 회원가입")
            with st.form(key="join_form"):
                new_id = st.text_input("사용할 아이디(ID)", placeholder="새로운 아이디 입력").strip()
                new_pw = st.text_input("사용할 비밀번호(Password)", type="password", placeholder="새로운 비밀번호 입력").strip()
                confirm_pw = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호 다시 입력").strip()
                submit_join = st.form_submit_button("가입 완료하기", use_container_width=True)
                
                if submit_join:
                    if not new_id or not new_pw: 
                        st.error("❌ 모든 칸을 입력해 주세요.")
                    elif db_load(f"users/{new_id}") is not None: 
                        st.error("❌ 이미 존재하는 아이디입니다.")
                    elif new_pw != confirm_pw: 
                        st.error("❌ 비밀번호가 일치하지 않습니다.")
                    else:
                        db_save(f"users/{new_id}", new_pw)
                        st.success("🎯 회원가입 완료! 로그인해 주세요.")
                        st.session_state.auth_mode = "로그인"
                        st.rerun()
            
            st.caption("이미 계정이 있으신가요?")
            if st.button("🔐 기존 아이디로 로그인하러 가기", use_container_width=True):
                st.session_state.auth_mode = "로그인"
                st.rerun()

# --- ✈️ 메인 프로그램 시작 ---
if not st.session_state.logged_in:
    show_auth_page()
else:
    user = st.session_state.current_user
    user_root = db_load(f"plans/{user}")
    
    if user_root is None:
        user_root = {
            "saved_trips": [],
            "current_trip": get_default_trip()
        }
        db_save(f"plans/{user}", user_root)
    
    with st.sidebar:
        st.write(f"👤 **접속 중:** `{user}` 님")
        if st.button("🔓 로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
        st.markdown("---")
        st.subheader("🧭 메뉴 이동")
        
        menu_list = ["🏠 홈 (플래너 짜기)", "👤 프로필 (내 저장 보관함)"]
        default_idx = menu_list.index(st.session_state.page_view) if st.session_state.page_view in menu_list else 0
        
        page = st.radio("이동할 페이지를 선택하세요", menu_list, index=default_idx, key="menu_radio")
        if page != st.session_state.page_view:
            st.session_state.page_view = page
            st.rerun()

    if st.session_state.page_view == "🏠 홈 (플래너 짜기)":
        user_data = user_root["current_trip"]
        
        if isinstance(user_data["start_date"], str):
            try:
                sd_obj = datetime.strptime(user_data["start_date"], "%Y-%m-%d").date()
            except:
                sd_obj = datetime.today().date()
        else:
            sd_obj = user_data["start_date"]

        with st.sidebar:
            st.markdown("---")
            st.header("⚙️ 여행 플래너 설정")
            user_data["trip_title"] = st.text_input("여행 제목", user_data["trip_title"])
            picked_date = st.date_input("시작 날짜", sd_obj)
            
            new_date_str = picked_date.strftime("%Y-%m-%d")
            if user_data["start_date"] != new_date_str:
                user_data["start_date"] = new_date_str
                db_save(f"plans/{user}/current_trip", user_data)
                st.rerun()
            
            st.markdown("---")
            st.subheader("📅 일정 관리")
            
            if st.button("➕ 다음 Day 추가하기", use_container_width=True):
                next_day_num = len(user_data["itinerary"]) + 1
                new_day_key = f"Day {next_day_num}"
                if new_day_key not in user_data["itinerary"]:
                    user_data["itinerary"][new_day_key] = {
                        "schedule": [], "image_base64": None, "notes": "", "meals": {"아침": "", "점심": "", "저녁": ""}
                    }
                    db_save(f"plans/{user}/current_trip", user_data)
                    st.rerun()

            if len(user_data["itinerary"]) > 1:
                if st.button("❌ 마지막 Day 삭제하기", use_container_width=True):
                    last_day_key = f"Day {len(user_data['itinerary'])}"
                    del user_data["itinerary"][last_day_key]
                    db_save(f"plans/{user}/current_trip", user_data)
                    st.rerun()

        sd_obj = datetime.strptime(user_data["start_date"], "%Y-%m-%d").date()

        st.title(f"🏠 여행 플래너 작성하기")
        
        # 🔄 헤더 영역: 여행 제목 및 전체 리셋 버튼 배치
        col_title, col_reset = st.columns([3.5, 0.5])
        with col_title:
            st.subheader(f"✈️ {user_data['trip_title']}")
            st.caption(f"📅 여행 시작일: {user_data['start_date']}")
        with col_reset:
            st.write("\n") # 간격 맞춤용
            if icon_button("🔄 전체리셋", key="total_reset_btn", help_text="현재 작성 중인 전체 플래너를 리셋합니다."):
                user_root["current_trip"] = get_default_trip()
                db_save(f"plans/{user}", user_root)
                st.rerun()

        col_save_box, _ = st.columns([2, 2])
        with col_save_box:
            if st.button("💾 이 여행 플래너를 내 프로필에 최종 저장하기", type="primary", use_container_width=True):
                if "saved_trips" not in user_root or not isinstance(user_root["saved_trips"], list):
                    user_root["saved_trips"] = []
                
                saved_item = json.loads(json.dumps(user_data))
                saved_item["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                saved_item["owner"] = user
                user_root["saved_trips"].append(saved_item)
                
                db_save(f"plans/{user}", user_root)
                st.success("🎯 프로필 보관함에 저장이 완료되었습니다!")

        st.markdown("---")

        day_keys = list(user_data["itinerary"].keys())
        tabs = st.tabs([f"📍 {day}" for day in day_keys])

        for i, day_key in enumerate(day_keys):
            with tabs[i]:
                this_day_date = sd_obj + timedelta(days=i)
                
                # 🔄 각 Day별 타이틀 및 해당 Day 리셋 버튼 배치
                col_day_head, col_day_reset = st.columns([3.4, 0.6])
                with col_day_head:
                    st.subheader(f"📅 {day_key} 일정 및 기록 ({this_day_date.strftime('%m월 %d일')})")
                with col_day_reset:
                    if icon_button("🧹 하루 비우기", key=f"reset_{day_key}", help_text=f"{day_key}의 모든 일정을 초기화합니다."):
                        user_data["itinerary"][day_key] = {
                            "schedule": [], "image_base64": None, "notes": "", "meals": {"아침": "", "점심": "", "저녁": ""}
                        }
                        db_save(f"plans/{user}/current_trip", user_data)
                        st.rerun()
                        
                col_left, col_right = st.columns([1.2, 0.8])
                
                with col_left:
                    st.markdown("### 🕒 순서별 이동 경로")
                    if "schedule" not in user_data["itinerary"][day_key]:
                        user_data["itinerary"][day_key]["schedule"] = []
                    schedules = user_data["itinerary"][day_key]["schedule"]
                    
                    if len(schedules) > 0:
                        for idx, item in enumerate(schedules):
                            # 📌 정렬 최적화: 조작부를 한데 모으거나 좌우 컬럼 높이를 맞춰 정렬이 흐트러지지 않게 개선
                            c_body, c_up, c_down, c_edit, c_del = st.columns([1.2, 0.07, 0.07, 0.07, 0.07])
                            
                            # 1. 중앙 본문 내용 표시
                            with c_body:
                                time_display = item['시간'] if item['시간'] else f"순서 {idx+1}"
                                memo_text = item.get('메모', '').strip()
                                st.markdown(f'<div class="schedule-container"><span style="color: #ff4b4b; font-weight: bold; font-size: 16px;">{time_display}</span> <span style="font-size: 16px; margin-left: 10px; font-weight: bold; color: #111111;">{item["장소"]}</span><div style="color: #555555; font-size: 14px; margin-top: 4px; padding-left: 2px;">📝 {memo_text if memo_text else "등록된 메모가 없습니다."}</div></div>', unsafe_allow_html=True)
                            
                            # 2. 오른쪽 조작 버튼들 (세로축이 틀어지지 않도록 동일한 컬럼 라인에 배치)
                            with c_up:
                                if idx > 0:
                                    if icon_button("🔼", key=f"up_{day_key}_{idx}", help_text="위로 이동"):
                                        schedules[idx], schedules[idx-1] = schedules[idx-1], schedules[idx]
                                        db_save(f"plans/{user}/current_trip", user_data)
                                        st.rerun()
                            with c_down:
                                if idx < len(schedules) - 1:
                                    if icon_button("🔽", key=f"down_{day_key}_{idx}", help_text="아래로 이동"):
                                        schedules[idx], schedules[idx+1] = schedules[idx+1], schedules[idx]
                                        db_save(f"plans/{user}/current_trip", user_data)
                                        st.rerun()
                            with c_edit:
                                edit_key = f"edit_active_{day_key}_{idx}"
                                if edit_key not in st.session_state:
                                    st.session_state[edit_key] = False
                                if icon_button("✏️", key=f"edit_btn_{day_key}_{idx}", help_text="내용 수정하기"):
                                    st.session_state[edit_key] = not st.session_state[edit_key]
                                    st.rerun()
                            with c_del:
                                if icon_button("❌", key=f"del_btn_{day_key}_{idx}", help_text="이 일정 삭제"):
                                    schedules.pop(idx)
                                    db_save(f"plans/{user}/current_trip", user_data)
                                    st.rerun()
                                    
                            # 수정 폼 활성화 시
                            if st.session_state.get(edit_key, False):
                                st.markdown("⚙️ **선택한 일정 수정하기**")
                                e_c1, e_c2 = st.columns([1, 2])
                                e_time = e_c1.text_input("시간 수정", value=item['시간'], key=f"e_time_{day_key}_{idx}")
                                e_place = e_c2.text_input("장소 수정", value=item['장소'], key=f"e_place_{day_key}_{idx}")
                                e_memo = st.text_area("메모 수정", value=item.get('메모',''), key=f"e_memo_{day_key}_{idx}")
                                
                                e_cx, e_cy = st.columns([1, 1])
                                e_mtype = e_cx.text_input("이동수단 수정", value=item.get('이동수단',''), key=f"e_mtype_{day_key}_{idx}")
                                e_mtime = e_cy.text_input("이동시간 수정", value=item.get('이동시간',''), key=f"e_mtime_{day_key}_{idx}")
                                
                                if st.button("✅ 변경사항 저장하기", key=f"e_save_{day_key}_{idx}", use_container_width=True):
                                    schedules[idx] = {
                                        "시간": e_time.strip(), "장소": e_place.strip(), "이동수단": e_mtype.strip(), "이동시간": e_mtime.strip(), "메모": e_memo
                                    }
                                    db_save(f"plans/{user}/current_trip", user_data)
                                    st.session_state[edit_key] = False
                                    st.success("성공적으로 수정되었습니다!")
                                    st.rerun()
                                        
                            # 📌 화살표 간격 및 여백 축소
                            if idx < len(schedules) - 1:
                                m_type_str = item.get('이동수단', '').strip()
                                m_time_str = item.get('이동시간', '').strip()
                                if m_type_str or m_time_str:
                                    combine_info = f"{m_type_str} ({m_time_str})" if m_type_str and m_time_str else (m_type_str or m_time_str)
                                    st.markdown(f'<div class="arrow-container"><span style="color:#ff4b4b; font-weight:bold; font-size:14px;">↓</span> &nbsp;<span style="font-size:12px; color:#222222; font-weight:600; background-color:#E8ECEF; padding:2px 8px; border-radius:20px;">{combine_info}</span></div>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<div class="arrow-container"><span style="color:#ff4b4b; font-weight:bold; font-size:14px;">↓</span></div>', unsafe_allow_html=True)
                    else:
                        st.info("등록된 일정이 없습니다. 아래에서 일정을 추가해보세요!")

                    st.markdown("---")
                    with st.expander("➕ 새로운 일정 추가하기", expanded=True):
                        if f"add_cnt_{day_key}" not in st.session_state:
                            st.session_state[f"add_cnt_{day_key}"] = 0
                        cnt = st.session_state[f"add_cnt_{day_key}"]

                        c1, c2 = st.columns([1, 2])
                        t_val = c1.text_input("시간 (선택)", key=f"t_in_{day_key}_{cnt}", placeholder="예: 11:00")
                        p_val = c2.text_input("장소/활동 명칭 *필수*", key=f"p_in_{day_key}_{cnt}", placeholder="예: 삿포로역")
                        m_val = st.text_area("일정 상세 메모", key=f"m_in_{day_key}_{cnt}", placeholder="상세 정보를 입력하세요.")
                        
                        cx, cy = st.columns([1, 1])
                        m_type_input = cx.text_input("다음 장소로 갈 때 이동 수단", key=f"mt_in_{day_key}_{cnt}", placeholder="예: JR 열차")
                        m_time_input = cy.text_input("이동 시간", key=f"mtime_in_{day_key}_{cnt}", placeholder="예: 40분")
                        
                        if st.button("💾 이 일정 최종 추가하기", key=f"save_add_{day_key}_{cnt}", use_container_width=True):
                            if p_val:
                                user_data["itinerary"][day_key]["schedule"].append({
                                    "시간": t_val.strip(), "장소": p_val.strip(), "이동수단": m_type_input.strip(), "이동시간": m_time_input.strip(), "메모": m_val
                                })
                                db_save(f"plans/{user}/current_trip", user_data)
                                st.session_state[f"add_cnt_{day_key}"] += 1
                                st.rerun()
                            else:
                                st.error("장소/활동 명칭은 필수 입력 항목입니다!")

                    st.markdown("---")
                    st.markdown("### 🍴 오늘 하루 식사 기록 (맛집)")
                    if "meals" not in user_data["itinerary"][day_key]: 
                        user_data["itinerary"][day_key]["meals"] = {"아침":"", "점심":"", "저녁":""}
                    current_meals = user_data["itinerary"][day_key]["meals"]
                    
                    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
                    b_input = f_col1.text_input("🍳 아침 메뉴", value=current_meals.get("아침", ""), key=f"b_input_{day_key}")
                    l_input = f_col2.text_input("🍱 점심 메뉴", value=current_meals.get("점심", ""), key=f"l_input_{day_key}")
                    d_input = f_col3.text_input("🍣 저녁 메뉴", value=current_meals.get("저녁", ""), key=f"d_input_{day_key}")
                    
                    if st.button("💾 오늘 식사 기록 저장", key=f"save_meals_{day_key}", use_container_width=True):
                        user_data["itinerary"][day_key]["meals"] = {"아침": b_input.strip(), "점심": l_input.strip(), "저녁": d_input.strip()}
                        db_save(f"plans/{user}/current_trip", user_data)
                        st.success("🍴 오늘의 식사 정보가 업데이트되었습니다!")
                        st.rerun()

                with col_right:
                    st.markdown("### 🖼️ 사진 및 자유 텍스트 기록")
                    uploaded_file = st.file_uploader("📸 사진 업로드", type=["png", "jpg", "jpeg"], key=f"img_{day_key}")
                    if uploaded_file is not None:
                        user_data["itinerary"][day_key]["image_base64"] = encode_image(uploaded_file)
                        db_save(f"plans/{user}/current_trip", user_data)
                        st.rerun()
                        
                    img_data = user_data["itinerary"][day_key].get("image_base64")
                    if img_data:
                        st.image(base64.b64decode(img_data), use_container_width=True)
                        if st.button("🖼️ 사진 지우기", key=f"del_img_{day_key}"):
                            user_data["itinerary"][day_key]["image_base64"] = None
                            db_save(f"plans/{user}/current_trip", user_data)
                            st.rerun()
                    
                    st.markdown("---")
                    current_notes = user_data["itinerary"][day_key].get("notes", "")
                    text_input = st.text_area("✍️ 기록/일기", value=current_notes, height=150, key=f"txt_{day_key}")
                    if st.button("💾 텍스트 기록 저장", key=f"save_txt_{day_key}"):
                        user_data["itinerary"][day_key]["notes"] = text_input
                        db_save(f"plans/{user}/current_trip", user_data)
                        st.success("저장 완료!")
                        st.rerun()

    elif st.session_state.page_view == "👤 프로필 (내 저장 보관함)":
        st.title("👤 내 프로필 및 플래너 보관함")
        st.write(f"안녕하세요, **{user}**님! 목록을 누르시면 해당 플래너를 가지고 바로 **🏠 홈 화면**으로 이동합니다.")
        st.markdown("---")

        saved_list = user_root.get("saved_trips", [])
        if not isinstance(saved_list, list): saved_list = []

        if len(saved_list) == 0:
            st.info("💡 아직 저장된 여행 플래너가 없습니다.")
        else:
            st.subheader(f"📁 내 저장 목록 ({len(saved_list)}개)")
            
            for idx, trip in enumerate(saved_list):
                with st.container():
                    c_title, c_date, c_del = st.columns([4, 2, 1])
                    if c_title.button(f"🗺️ {trip['trip_title']}", key=f"trip_btn_{idx}", use_container_width=True):
                        # 📌 [개선 핵심]: 현재 작업 중인 플래너에 선택한 데이터를 덮어씌운 후 세션 상태 변경 + 즉각 화면 갱신
                        user_root["current_trip"] = json.loads(json.dumps(trip))
                        db_save(f"plans/{user}", user_root)
                        st.session_state.page_view = "🏠 홈 (플래너 짜기)"
                        st.rerun()
                        
                    c_date.write(f"📅 시작일: `{trip['start_date']}`\n\n⏱️ 저장일: {trip['saved_at']}")
                    if c_del.button("🗑️ 삭제", key=f"p_del_{idx}", use_container_width=True):
                        user_root["saved_trips"].pop(idx)
                        db_save(f"plans/{user}", user_root)
                        st.success("목록에서 삭제되었습니다.")
                        st.rerun()
                        
                    st.markdown("<div style='border-bottom: 1px solid #eee; margin: 10px 0;'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("🗺️ 여행 플래너 - 클라우드 DB 연동 완료.")
