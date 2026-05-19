#uv run streamlit run frontend/app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000"

if "page" not in st.session_state:
    st.session_state["page"] = "問い合わせ入力"
#############
if st.session_state["page"] != "detail":
    st.sidebar.title("メニュー")
    selected_page = st.sidebar.radio(
        "ページ", 
        ["問い合わせ入力", "問い合わせ一覧"],
        index=0 if st.session_state["page"] == "問い合わせ入力" else 1
    )
    st.session_state["page"] = selected_page
#############
if st.session_state["page"] == "問い合わせ入力":
    st.title("AI問い合わせ管理アプリ")
    st.subheader("問い合わせ入力画面")

    question = st.text_area("問い合わせ内容を入力してください", height=150)

    if st.button("送信する"):
        if question.strip() == "":
            st.error("問い合わせ内容を入力してください。")
        else:
            try:
                response = requests.post(f"{API_URL}/inquiries", json={"question": question})
                if response.status_code == 201:

                    data = response.json()
                    
                    st.success("✅ 問い合わせを送信しました")
                    st.write("---")
                    st.write(f"**カテゴリ：** {data.get('category')}")
                    st.write(f"**緊急度：** {data.get('urgency')}")
                    st.write(f"**回答案：** {data.get('answer')}")
                    
                else:
                    st.error("AI分析または保存に失敗しました。")
            except requests.exceptions.ConnectionError:
                st.error("バックエンドに接続できません")
#############
elif st.session_state["page"] == "問い合わせ一覧":
    st.title("AI問い合わせ管理アプリ")
    st.subheader("問い合わせ内容一覧")

    try:
        response = requests.get(f"{API_URL}/inquiries")
        if response.status_code == 200:
            inquiries = response.json()
            if len(inquiries) == 0:
                st.info("問い合わせがありません")
            else:
                header_col1, header_col2 = st.columns([3, 7])
                with header_col1:
                    st.write("**問い合わせ日時**")
                with header_col2:
                    st.write("**問い合わせ内容**")
                st.divider()

                for item in inquiries:
                    col1, col2, col3 = st.columns([3, 5, 2])
                    with col1:
                        formatted_date = item["created_at"][:16].replace("T", " ")
                        st.write(formatted_date)
                    with col2:
                        st.write(item["question"])
                    with col3:
                        if st.button("詳細を見る", key=item["id"]):
                            st.session_state["selected_id"] = item["id"]
                            st.session_state["page"] = "detail"
                            st.rerun()
        else:
            st.error("一覧取得に失敗しました")
    except requests.exceptions.ConnectionError:
        st.error("バックエンドに接続できません")
##############
elif st.session_state["page"] == "detail":
    st.title("AI問い合わせ管理アプリ")
    st.subheader("問い合わせ内容詳細")
    st.divider()
    
    inquiry_id = st.session_state.get("selected_id")

    try:
        response = requests.get(f"{API_URL}/inquiries/{inquiry_id}")
        if response.status_code == 200:
            data = response.json()
            st.write("【問い合わせ内容】")
            st.write(data["question"])
            
            formatted_date = data["created_at"][:19].replace("T", " ")
            st.write(f"問い合わせ日時：{formatted_date}")
            st.write(f"カテゴリ：{data['category']}")
            st.write(f"緊急度：{data['urgency']}")
            st.write(f"回答案：{data['answer']}")
            
            st.write("")
            st.write("")
            
            if st.button("← 一覧に戻る"):
                st.session_state["page"] = "問い合わせ一覧"
                st.rerun()
        elif response.status_code == 404:
            st.error("指定された問い合わせが見つかりません")
            if st.button("← 一覧に戻る"):
                st.session_state["page"] = "問い合わせ一覧"
                st.rerun()
        else:
            st.error("詳細の取得に失敗しました")
    except requests.exceptions.ConnectionError:
        st.error("バックエンドに接続できません")