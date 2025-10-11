import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
import json
import re

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

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    country = data.get("country", "")
    theme = data.get("theme", "관광")

    # AI prompt (JSON escape 적용 강제)
    prompt = f"""
{country}에서 {theme} 테마에 맞는 여행지 3곳을 추천해줘.
- 반드시 JSON 배열로 반환
- 문자열은 모두 큰따옴표(") 사용
- description 내부 모든 특수문자와 줄바꿈은 JSON-safe하게 처리
- 형식:
[
  {{"name": "여행지명", "region": "지역", "description": "간단한 설명"}}
]
"""

    try:
        # Gemini 호출
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # 작은따옴표 → 큰따옴표, 줄바꿈 제거
        text = text.replace("'", '"').replace("\n", " ")

        # JSON 배열 추출
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                travel_data = json.loads(match.group(0))
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 fallback
                travel_data = [
                    {"name": "추천 여행지1", "region": country, "description": "설명 없음"},
                    {"name": "추천 여행지2", "region": country, "description": "설명 없음"},
                    {"name": "추천 여행지3", "region": country, "description": "설명 없음"}
                ]
        else:
            travel_data = [
                {"name": "추천 여행지1", "region": country, "description": "설명 없음"},
                {"name": "추천 여행지2", "region": country, "description": "설명 없음"},
                {"name": "추천 여행지3", "region": country, "description": "설명 없음"}
            ]

        # Unsplash 이미지 추가
        for place in travel_data:
            query = f"{place['name']} {place.get('region','')} {country}"
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
        # AI 호출 실패 fallback
        return jsonify([
            {"name": "추천 여행지", "region": country,
             "description": f"⚠ AI 호출 실패: {e}",
             "image": "https://via.placeholder.com/400x250"}
        ])

if __name__ == "__main__":
    app.run(debug=True)
