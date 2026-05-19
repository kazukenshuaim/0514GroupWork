# uv run uvicorn backend.main:app --reload
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import os
import json
from dotenv import load_dotenv

# 新しいGoogle GenAI SDKをインポート
from google import genai
from google.genai import types

from backend.storage import read_inquiries, write_inquiries

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 新しい方式でGeminiクライアントを初期化
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = FastAPI()

class InquiryRequest(BaseModel):
    question: str

class InquiryRecord(BaseModel):
    id: int
    created_at: str
    question: str
    answer: str
    category: str
    urgency: str

def analyze_with_gemini(question: str):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini APIキーが設定されていません")
        
    system_prompt = """
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
    勤怠, 休暇, 給与, 経費精算, 社員情報変更, その他
    """
    
    try:
        # 新しいSDKの関数呼び出し形式に変更（推奨モデル: gemini-2.5-flash）
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            )
        )
        
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:-3]
            
        return json.loads(result_text)
    except Exception as e:
        # ターミナル側で具体的なエラー内容を確認できるようにログを出力
        print(f"Gemini API Error: {e}")
        raise HTTPException(status_code=500, detail="Gemini APIとの通信に失敗しました")

@app.post("/inquiries", status_code=201)
def create_inquiry(req: InquiryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="問い合わせ内容が空です")

    data = read_inquiries()
    new_id = 1 if len(data) == 0 else max(item["id"] for item in data) + 1
    
    JST = timezone(timedelta(hours=+9), 'JST')
    created_at = datetime.now(JST).isoformat()

    ai_result = analyze_with_gemini(req.question)

    new_record = {
        "id": new_id,
        "created_at": created_at,
        "question": req.question,
        "answer": ai_result.get("answer", "回答を生成できませんでした"),
        "category": ai_result.get("category", "その他"),
        "urgency": ai_result.get("urgency", "中")
    }

    data.append(new_record)
    write_inquiries(data)
    return new_record

@app.get("/inquiries")
def get_inquiries():
    data = read_inquiries()
    # 降順（新しい順）に並べ替え
    sorted_data = sorted(data, key=lambda x: x["id"], reverse=True)
    return sorted_data

@app.get("/inquiries/{inquiry_id}")
def get_inquiry_detail(inquiry_id: int):
    data = read_inquiries()
    for item in data:
        if item["id"] == inquiry_id:
            return item
    raise HTTPException(status_code=404, detail="指定された問い合わせが見つかりません")