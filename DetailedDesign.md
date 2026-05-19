# 詳細設計書

**プロジェクト名：** AI問い合わせ管理アプリ   
**作成日：** 2026-05-15  
**対象研修：** AI問い合わせ管理アプリ開発研修

## 1. API仕様

### 1.1. POST /inquiries 問い合わせをJSONファイルに保存する

**概要：** 新規の問い合わせを入力、送信するとAIが回答、カテゴリ、緊急度を返す。

**リクエスト：**

```
POST http://localhost:8000/inquiries
Content-Type: application/json
```

```json
{
    "question": "電話番号を変更しました。"
}
```

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| question | 文字列 | ○ | 問い合わせ本文（空不可）|

**レスポンス（成功 201）:**

```json
{
    "id": 2,
    "created_at": "2026-05-14T10:00:00+9:00",
    "question": "電話番号を変更しました。",
    "answer": "どんまい",
    "category": "社員情報変更",
    "urgency": "中"
}
```

**エラーレスポンス:**
| ステータス | 発生条件 |
|---|---|
| 422 | JSONの内容が不正 |
| 500 | サーバーの内部のエラー |

### 1.2. GET /inquiries 問い合わせ一覧を返す

**概要：** 送信済みのタスクを全件、問い合わせ日時の降順（新しい順）で返す。

**リクエスト：**
```
GET http://localhost:8000/inquiries
```

**レスポンス（成功 200）:**
```json
[
    {
        "id": 2,
        "created_at": "2026-05-14T10:00:00+9:00",
        "question": "電話番号を変更しました。",
        "answer": "どんまい",
        "category": "社員情報変更",
        "urgency": "中"
    },
    {
        "id": 1,
        "created_at": "2026-05-13T14:30:00+9:00",
        "question": "運転免許証をなくした。",
        "answer": "再発行しよう",
        "category": "その他",
        "urgency": "高"
    }
]
```
- 問い合わせが0件のときは、空のリスト`[]`を返す

**エラーレスポンス:**
| ステータス | 発生条件 |
|---|---|
| 500 | サーバーの内部のエラー |

### 1.3. GET /inquiries/{id} 指定IDの問い合わせを返す

**概要：** 指定IDの問い合わせの詳細を1件返す。

**リクエスト：**
```
GET http://localhost:8000/inquiries/1
```

**レスポンス（成功 200）:**

```json
{
    "id": 2,
    "created_at": "2026-05-14T10:00:00+9:00",
    "question": "電話番号を変更しました。",
    "answer": "どんまい",
    "category": "社員情報変更",
    "urgency": "中"
}
```

**エラーレスポンス:**
| ステータス | 発生条件 |
|---|---|
| 404 | 指定したIDが存在しない |
| 500 | サーバーの内部のエラー |

## 2. データモデル

```Python
from pydantic import BaseModel

class InquiryRequest(BaseModel):
    question: str          # POST リクエストボディ

class InquiryRecord(BaseModel):
    id: int
    created_at: str
    quesition: str
    answer: str
    category: str
    urgency: str
```
## 3. 外部連携仕様

### 3.1 プロンプト設計

**送信するプロンプト**

```Python
システムプロンプト：
  あなたは社内の総務部門向け問い合わせ分類AIアシスタントです。
  社員からの問い合わせ文を受け取り、以下のJSON形式のみで回答してください。
  余分な説明や前置きは不要です。

  出力形式：
  {
    "category": "カテゴリ名",
    "urgency": "高 または 中 または 低",
    "answer": "一次回答文"
  }

  カテゴリは以下の中から最も適切な1つを選んでください：
  勤怠, 休暇, 給与, 経費精算, 社員情報, その他

ユーザーメッセージ：
  {問い合わせ本文（そのまま渡す）}
```


### 3.2 処理手順

1. **リクエスト受信**: FastAPIがフロントエンドから送信された問い合わせ本文（`question`）を受け取る。
2. **API初期化**: 環境変数（`.env`）から読み込んだ `GEMINI_API_KEY` を使用して、Gemini APIのクライアントを初期化する。
3. **推論リクエスト**: 対象モデル（`gemini-2.5-flash`）に対し、3.1で定義したシステムプロンプトとユーザーからの問い合わせ本文を送信する。
4. **レスポンス取得**: Gemini APIから生成されたテキストデータを受け取る。
5. **データ整形（パース）**: 返却されたテキストから不要な文字（マークダウンの ```json 記法など）を取り除き、JSONオブジェクトとしてパースして「カテゴリ」「緊急度」「回答案」を抽出する。
6. **例外処理**: APIとの通信に失敗した場合、またはJSONのパースに失敗した場合は、HTTPステータスコード500（Internal Server Error）をフロントエンドに返す。
---

## 4. データ操作処理

### 4.1. 全件読み込み

1. DATA_FILE_PATH のファイルが存在するか確認する
2. 存在しない場合は空のリスト [] を返す
3. 存在する場合は json.load() で読み込む
4. リストを返す

### 4.2. 問い合わせ送信

1. 全件読み込みを行いリストを取得する
2. 新しいレコードをリストの末尾に append する
3. json.dump() でファイルに上書き保存する
   （オプション：ensure_ascii=False, indent=2）

### 4.3. 一覧表示

1. DATA_FILE_PATH のファイルが存在するか確認する
2. 存在しない場合は空のリスト [] を返す
3. 存在する場合は json.load() で読み込んでリストを取得する
4. IDの降順（新しい順）に並べ替えてリストに再代入する
    （sorted(data, key=lambda x: x["ID"], reverse=True)を用いる）
5. リストを返す

### 4.4. 詳細表示

1. 全件読み込みを行いリストを取得する
2. 指定したIDが一致するレコードを検索する
3. 見つかれば返す。見つからなければNoneを返す

---

## 5. 画面詳細

### 5.1. サイドバー

```Python
st.sidebar.title("メニュー")
page = st.sidebar.radio("ページ", ["問い合わせ入力", "問い合わせ一覧"])
```

### 5.2. 問い合わせ入力画面

```Python
if page == "問い合わせ入力画面":

    st.title("AI問い合わせ管理アプリ")

    st.subheader("問い合わせ入力画面")

    question = st.text_area(
        "問い合わせ内容を入力してください",
        height=150
    )

    if st.button("送信する"):
        if question.strip() == "":
            st.error("問い合わせ内容を入力してください。")

        else:
            response = POST /inquiries に question を送信
            if response.ok:
                data = response.json()
                st.success("問い合わせを送信しました")
                st.write("カテゴリ：", data["category"])
                st.write("緊急度：", data["urgency"])
                st.write("回答案：", data["answer"])
            else:
                st.error("送信に失敗しました")
```

### 5.3. 一覧画面

```Python
st.title("AI問い合わせ管理アプリ")

st.subheader("問い合わせ内容一覧")

try:
    response = requests.get(
        f"{API_URL}/inquiries"
    )
    if response.status_code == 200:
        inquiries = response.json()
        if len(inquiries) == 0:
            st.info("問い合わせがありません")

        else:
            col1, col2, col3 = st.columns([2, 4, 2])
            with col1:
                st.write("問い合わせ日時")
            with col2:
                st.write("問い合わせ内容")
            with col3:
                st.write("詳細")
            st.divider()
            for item in inquiries:
                col1, col2, col3 = st.columns([2, 4, 2])
                with col1:
                    st.write(item["created_at"])
                with col2:
                    st.write(item["question"])
                with col3:
                    if st.button(
                        "詳細を見る",
                        key=item["id"]
                    ):
                        st.session_state["selected_id"] = item["id"]
                        st.session_state["page"] = "detail"
                        st.rerun()
    else:
        st.error("一覧取得に失敗しました")
except Exception:
    st.error("バックエンドに接続できません")


```

### 5.4. 詳細画面

```Python
st.title("AI問い合わせ管理アプリ")
st.subheader("問い合わせ内容詳細")
inquiry_id = st.session_state.get("selected_id")

try:
    response = requests.get(
        f"{API_URL}/inquiries/{inquiry_id}"
    )
    if response.status_code == 200:
        data = response.json()
        st.divider()
        st.write("【問い合わせ内容】")
        st.write(data["question"])
        st.write("問い合わせ日時：", data["created_at"])
        st.write("カテゴリ：", data["category"])
        st.write("緊急度：", data["urgency"])
        st.write("回答案：", data["answer"])
        st.write("")
        st.write("")
        if st.button("← 一覧に戻る"):
            st.session_state["page"] = "list"
            st.rerun()
    elif response.status_code == 404:

        st.error("指定された問い合わせが見つかりません")
    else:

        st.error("詳細取得に失敗しました")
except Exception:

    st.error("バックエンドに接続できません")
if page == "問い合わせ入力画面":

    st.title("AI問い合わせ管理アプリ")

    st.subheader("問い合わせ入力画面")

    question = st.text_area(
        "問い合わせ内容を入力してください",
        height=150
    )

    if st.button("送信する"):
        if question.strip() == "":
            st.error("問い合わせ内容を入力してください。")
        else:
            response = POST /inquiries に question を送信
            if response.ok:
                data = response.json()
                st.success("問い合わせを送信しました")
                st.write("カテゴリ：", data["category"])
                st.write("緊急度：", data["urgency"])
                st.write("回答案：", data["answer"])
            else:

                st.error("送信に失敗しました")

```

---

## 6. エラー処理一覧

| No | 発生箇所 | エラー内容 | 処理内容 | ユーザー表示 |
|---:|---|---|---|---|
| 1 | Streamlit | 問い合わせ内容が空のまま送信 | APIを呼ばずに停止 | 「問い合わせ内容を入力してください。」 |
| 2 | FastAPI | inquiries.jsonが存在しない | 空リストとして処理を続行 | （エラーなし。履歴画面では「履歴はありません」と表示） |
| 3 | FastAPI | Gemini APIの通信失敗 | 500エラーを返す | 「AI分析または保存に失敗しました。」 |

---

## 7. テスト観点

### 7.1 正常系テスト

| No | テスト内容 | 確認ポイント |
|---:|---|---|
| 1 | 問い合わせを入力して送信する | AIの分析結果（カテゴリ等）が画面に正しく表示されること |
| 2 | 履歴画面を開く | さきほど送信した問い合わせが一覧の一番上に表示されること |
| 3 | JSONファイルの確認 | `data/inquiries.json` に新しいデータが追記され、IDが連番で増えていること |

### 7.2 異常系テスト

| No | テスト内容 | 確認ポイント |
|---:|---|---|
| 5 | 入力欄を空にして送信ボタンを押す | エラーメッセージが表示され、APIが呼ばれないこと |
| 6 | inquiries.jsonがない状態で履歴を開く | エラーで落ちず、「履歴はありません」と表示されること |