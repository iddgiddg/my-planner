import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import base64

# 1. 웹페이지 기본 설정 (요청하신 대로 이름을 '여행 플래너'로 변경했습니다)
st.set_page_config(page_title="여행 플래너 ✈️", page_icon="✈️", layout="wide")

# ⭐ 본인의 파이어베이스 Realtime Database 주소를 여기에 입력해 주세요.
FIREBASE_URL = "https://my-planner-fc3a5-default-rtdb.firebaseio.com/"

# --- 🌐 파이어베이스 통신용 함수 정의 ---
def db_save(path, data):
    """파이어베이스의 특정 경로에 데이터를 저장합니다."""
    try:
        url = f"{FIREBASE_URL}{path}.json"
        response = requests.put(url, json=data)
        return response.status_code == 200
    except:
        return False

def db_load(path):
    """파이어베이스의 특정 경로에서 데이터를 불러옵니다."""
    try:
        url = f"{FIREBASE_URL}{path}.json"
        response = requests.get(url)
        if response.status_code == 200 and response.text != "null":
            return response.json()
    except:
        pass
    return None

# 사진 데이터를 DB에 글자 형태로 저장하기 위한 인코딩 함수
def encode_image(file):
    if file is not None:
        return base64.b64encode(file.getvalue()).decode()
    return None

# 2. 로컬 세션 상태 관리 초기화
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = "로그인"
if 'page_view' not in st.session_state: st.session_state.page_view = "🏠 홈 (플래너 짜기)"

# --- 🔐 인증 시스템 화면 (오류가 발생하는 라디오 버튼 대신 깔끔한 버튼 전환형으로 수정) ---
def show_auth_page():
    st.markdown("<h2 style='text-align: center; margin-bottom: 25px;'>✈️ 영구 저장형 여행 플래너</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # 로그인 모드일 때
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
            
            # 회원가입 전환 버튼
            st.caption("아직 계정이 없으신가요?")
            if st.button("📝 새로운 회원가입 하러가기", use_container_width=True):
                st.session_state.auth_mode = "회원가입"
                st.rerun()
                        
        # 회원가입 모드일 때
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
            
            # 로그인 전환 버튼
            st.caption("이미 계정이 있으신가요?")
            if st.button("🔐 기존 아이디로 로그인하러 가기", use_container_width=True):
                st.session_state.auth_mode = "로그인"
                st.rerun()

# --- ✈️ 메인 플래너 프로그램 코드 ---
if not st.session_state.logged_in:
    show_auth_page()
else:
    user = st.session_state.current_user
    
    # 로그인한 사용자의 데이터를 DB에서 조회 및 기본값 생성
    user_root = db_load(f"plans/{user}")
    if user_root is None:
        user_root = {
            "saved_trips": [],
            "current_trip": {
                "trip_title": "나의 특별한 여행",
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "itinerary": {
                    "Day 1": {
                        "schedule": [], "image_base64": None, "notes": "", "meals": {"아침": "", "점심": "", "저녁": ""}
                    }
                }
            }
        }
        db_save(f"plans/{user}", user_root)
    
    # 사이드바 메뉴 이동
    with st.sidebar:
        st.write(f"👤 **접속 중:** `{user}` 님")
        if st.button("🔓 로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
        st.markdown("---")
        st.subheader("🧭 메뉴 이동")
        page = st.radio("이동할 페이지를 선택하세요", ["🏠 홈 (플래너 짜기)", "👤 프로필 (내 저장 보관함)"])
        st.session_state.page_view = page

    # ==================== 🏠 홈 페이지 (여행 플래너 짜기) ====================
    if st.session_state.page_view == "🏠 홈 (플래너 짜기)":
        user_data = user_root["current_trip"]
        
        if isinstance(user_data["start_date"], str):
            sd_obj = datetime.strptime(user_data["start_date"], "%Y-%m-%d").date()
        else:
            sd_obj = user_data["start_date"]

        with st.sidebar:
            st.markdown("---")
            st.header("⚙️ 현재 여행 설정")
            user_data["trip_title"] = st.text_input("여행 제목", user_data["trip_title"])
            picked_date = st.date_input("시작 날짜", sd_obj)
            user_data["start_date"] = picked_date.strftime("%Y-%m-%d")
            
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

        st.title(f"🏠 여행 플래너 작성하기")
        st.subheader(f"✈️ {user_data['trip_title']}")
        st.caption(f"📅 여행 시작일: {user_data['start_date']}")

        col_save_box, _ = st.columns([2, 2])
        with col_save_box:
            if st.button("💾 이 여행 플래너를 내 프로필에 최종 저장하기", type="primary", use_container_width=True):
                if "saved_trips" not in user_root or not isinstance(user_root["saved_trips"], list):
                    user_root["saved_trips"] = []
                
                saved_item = json.loads(json.dumps(user_data))
                saved_item["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_root["saved_trips"].append(saved_item)
                
                db_save(f"plans/{user}", user_root)
                st.success("🎯 프로필 보관함에 영구 저장이 완료되었습니다!")

        st.markdown("---")

        day_keys = list(user_data["itinerary"].keys())
        tabs = st.tabs([f"📍 {day}" for day in day_keys])

        for i, day_key in enumerate(day_keys):
            with tabs[i]:
                this_day_date = sd_obj + timedelta(days=i)
                st.subheader(f"📅 {day_key} 일정 및 기록 ({this_day_date.strftime('%m월 %d일')})")
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    st.markdown("### 🕒 순서별 이동 경로")
                    if "schedule" not in user_data["itinerary"][day_key]:
                        user_data["itinerary"][day_key]["schedule"] = []
                    schedules = user_data["itinerary"][day_key]["schedule"]
                    
                    if len(schedules) > 0:
                        schedules_sorted = sorted(schedules, key=lambda x: (x['시간'] == "", x['시간']))
                        for idx, item in enumerate(schedules_sorted):
                            time_display = item['시간'] if item['시간'] else f"순서 {idx+1}"
                            memo_text = item.get('메모', '').strip()
                            st.markdown(f'<div style="background-color: #FFFFFF; padding: 14px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-top: 6px; margin-bottom: 6px; box-shadow: 0px 2px 4px rgba(0,0,0,0.05);"><span style="color: #ff4b4b; font-weight: bold; font-size: 16px;">{time_display}</span> <span style="font-size: 16px; margin-left: 10px; font-weight: bold; color: #111111;">{item["장소"]}</span><div style="color: #555555; font-size: 14px; margin-top: 6px; padding-left: 2px;">📝 {memo_text if memo_text else "등록된 메모가 없습니다."}</div></div>', unsafe_allow_html=True)
                            
                            if idx < len(schedules_sorted) - 1:
                                m_type_str = item.get('이동수단', '').strip()
                                m_time_str = item.get('이동시간', '').strip()
                                if m_type_str or m_time_str:
                                    combine_info = f"{m_type_str} ({m_time_str})" if m_type_str and m_time_str else (m_type_str or m_time_str)
                                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#ff4b4b; font-weight:bold; font-size:16px;'>↓</span> &nbsp;<span style='font-size:14px; color:#222222; font-weight:600; background-color:#E8ECEF; padding:3px 10px; border-radius:20px;'>{combine_info}</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#ff4b4b; font-weight:bold; font-size:16px;'>↓</span>", unsafe_allow_html=True)
                        
                        with st.expander("🗑️ 일정 삭제하기"):
                            for idx, item in enumerate(schedules):
                                col_t, col_p, col_b = st.columns([1, 3, 1])
                                col_t.write(f"**{item['시간'] if item['시간'] else '시간 미지정'}**")
                                col_p.write(f"{item['장소']}")
                                if col_b.button("삭제", key=f"del_{day_key}_{idx}"):
                                    user_data["itinerary"][day_key]["schedule"].pop(idx)
                                    db_save(f"plans/{user}/current_trip", user_data)
                                    st.rerun()
                    else:
                        st.info("등록된 일정이 없습니다.")

                    st.markdown("---")
                    with st.expander("➕ 새로운 일정 추가하기"):
                        c1, c2 = st.columns([1, 2])
                        t_val = c1.text_input("시간 (비워두면 자동 순서 배치)", key=f"time_in_{day_key}", placeholder="예: 11:00")
                        p_val = c2.text_input("장소/활동 명칭 *필수*", key=f"place_in_{day_key}", placeholder="예: 삿포로역")
                        
                        st.markdown("**🍴 오늘의 식사 기록 (선택 입력)**")
                        f1, f2, f3 = st.columns([1, 1, 1])
                        b_meal = f1.text_input("아침 메뉴", key=f"b_{day_key}", placeholder="예: 편의점 샌드위치")
                        l_meal = f2.text_input("점심 메뉴", key=f"l_{day_key}", placeholder="예: 잇핀 부타동")
                        d_meal = f3.text_input("저녁 메뉴", key=f"d_{day_key}", placeholder="예: 토리톤 스시")
                        
                        m_val = st.text_area("일정 상세 메모", key=f"memo_in_{day_key}", placeholder="상세 정보를 입력하세요.")
                        
                        cx, cy = st.columns([1, 1])
                        m_type_input = cx.text_input("다음 장소로 갈 때 이동 수단", key=f"m_type_{day_key}", placeholder="예: JR 열차")
                        m_time_input = cy.text_input("이동 시간", key=f"m_time_{day_key}", placeholder="예: 40분")
                        
                        if st.button("💾 이 일정 최종 저장하기", key=f"save_all_{day_key}", use_container_width=True):
                            if p_val:
                                if "schedule" not in user_data["itinerary"][day_key]: user_data["itinerary"][day_key]["schedule"] = []
                                user_data["itinerary"][day_key]["schedule"].append({
                                    "시간": t_val.strip(), "장소": p_val.strip(), "이동수단": m_type_input.strip(), "이동시간": m_time_input.strip(), "메모": m_val
                                })
                                user_data["itinerary"][day_key]["meals"] = {"아침": b_meal.strip(), "점심": l_meal.strip(), "저녁": d_meal.strip()}
                                db_save(f"plans/{user}/current_trip", user_data)
                                st.rerun()
                            else:
                                st.error("장소/활동 명칭은 필수 입력 항목입니다!")

                    st.markdown("---")
                    st.markdown("### 🍴 오늘 기록된 맛집 목록")
                    if "meals" not in user_data["itinerary"][day_key]: user_data["itinerary"][day_key]["meals"] = {"아침":"", "점심":"", "저녁":""}
                    current_meals = user_data["itinerary"][day_key]["meals"]
                    
                    if current_meals.get("아침") or current_meals.get("점심") or current_meals.get("저녁"):
                        m_parts = []
                        if current_meals.get("아침"): m_parts.append(f"🍳 아침: {current_meals['아침']}")
                        if current_meals.get("점심"): m_parts.append(f"🍱 점심: {current_meals['점심']}")
                        if current_meals.get("저녁"): m_parts.append(f"🍣 저녁: {current_meals['저녁']}")
                        st.markdown(f'<div style="background-color: #F1F8F5; padding: 14px; border-radius: 8px; border-left: 5px solid #2e7d32; margin-bottom: 12px; font-size: 14px; color: #2e7d32;">{" &nbsp;|&nbsp; ".join(m_parts)}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("등록된 식사 기록이 없습니다. 일정 추가하기 메뉴에서 함께 입력해 보세요!")

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

    # ==================== 👤 프로필 페이지 (내 저장 보관함) ====================
    elif st.session_state.page_view == "👤 프로필 (내 저장 보관함)":
        st.title("👤 내 프로필 및 플래너 보관함")
        st.write(f"안녕하세요, **{user}**님! 구글 실시간 DB에 동기화된 안전한 보관함입니다.")
        st.markdown("---")

        saved_list = user_root.get("saved_trips", [])
        if not isinstance(saved_list, list): saved_list = []

        if len(saved_list) == 0:
            st.info("💡 아직 영구 저장된 여행 플래너가 없습니다. 홈 화면에서 플래너를 저장해 보세요!")
        else:
            st.subheader(f"🗂️ 총 {len(saved_list)}개의 저장된 여행 목록")
            for idx, trip in enumerate(saved_list):
                c_title, c_date, c_time, c_action = st.columns([2, 1, 1, 1])
                c_title.write(f"🗺️ **{trip['trip_title']}**")
                c_date.write(f"📅 시작일: {trip['start_date']}")
                c_time.write(f"⏱️ 저장일시: `{trip['saved_at']}`")
                
                if c_action.button("📂 불러오기", key=f"load_trip_{idx}", use_container_width=True):
                    user_root["current_trip"] = json.loads(json.dumps(trip))
                    db_save(f"plans/{user}/current_trip", user_root["current_trip"])
                    st.success("🔄 플래너를 홈 화면으로 성공적으로 불러왔습니다!")
                    st.session_state.page_view = "🏠 홈 (플래너 짜기)"
                    st.rerun()
                st.markdown("<div style='border-bottom: 1px dashed #ddd; margin: 10px 0;'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("🗺️ 여행 플래너 - Google Firebase 실시간 클라우드 DB 연동 완료.")