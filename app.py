import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
import json
import re
import random

app = Flask(__name__)

# 환경 변수
gemini_key = os.getenv("GEMINI_API_KEY")
unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
if not gemini_key or not unsplash_key:
    raise ValueError("❌ GEMINI_API_KEY 또는 UNSPLASH_ACCESS_KEY가 설정되지 않았습니다!")

# Gemini API 설정
genai.configure(api_key=gemini_key)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/theme")
def theme():
    return render_template("theme.html")  # templates/theme.html 필요

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    theme = data.get("theme", "관광")

    # AI 프롬프트: 해외 여행지만 추천, 나라 중복 방지
    prompt = f"""
{theme} 테마에 맞는 해외 여행지 3곳을 추천해줘.
- 해외 국가만 선택
- 추천하는 여행지의 국가는 중복되지 않게
- 반드시 JSON 배열로 반환
- 문자열은 큰따옴표(") 사용
- description 내부 모든 특수문자와 줄바꿈은 JSON-safe하게 처리
- 형식:
[
  {{"name": "여행지명", "country": "나라", "description": "간단한 설명"}}
]
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = text.replace("'", '"').replace("\n", " ")

        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                travel_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                travel_data = []
        else:
            travel_data = []

        # fallback: 데이터 없으면 기본값
        if not travel_data:
            travel_data = [
                {"name": "파리", "country": "프랑스", "description": "설명 없음"},
                {"name": "로마", "country": "이탈리아", "description": "설명 없음"},
                {"name": "바르셀로나", "country": "스페인", "description": "설명 없음"}
            ]

        # Unsplash 이미지 추가
        for place in travel_data:
            query = f"{place['name']} {place['country']}"
            try:
                res = requests.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": query, "client_id": unsplash_key, "per_page": 1}
                )
                if res.status_code == 200 and res.json().get("results"):
                    place["image"] = res.json()["results"][0]["urls"]["regular"]
                else:
                    place["image"] = "https://via.placeholder.com/400x250?text=No+Image"
            except:
                place["image"] = "https://via.placeholder.com/400x250?text=No+Image"

        return jsonify(travel_data)

    except Exception as e:
        return jsonify([
            {"name": "추천 여행지", "country": "해외",
             "description": f"⚠ AI 호출 실패: {e}",
             "image": "https://via.placeholder.com/400x250"}
        ])

if __name__ == "__main__":
    app.run(debug=True)
