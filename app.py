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

@app.route("/theme")
def theme():
    return render_template("theme.html")

@app.route("/region")
def region():
    return render_template("region.html")  # templates/region.html 필요

# 기존 테마 추천 API
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    theme = data.get("theme")
    continent = data.get("continent")
    subregion = data.get("subregion")
    country = data.get("country")

    prompt_parts = []
    if theme:
        prompt_parts.append(f"{theme} 테마")
    if continent:
        prompt_parts.append(f"대륙: {continent}")
    if subregion:
        prompt_parts.append(f"하위 지역: {subregion}")
    if country:
        prompt_parts.append(f"국가: {country}")

    context = ", ".join(prompt_parts) if prompt_parts else "관광"

    prompt = f"""
{context}에 맞는 해외 여행지 3곳을 추천해줘.
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
        text = response.text.strip().replace("'", '"').replace("\n", " ")

        match = re.search(r'\[.*\]', text, re.DOTALL)
        travel_data = json.loads(match.group(0)) if match else []

        # fallback
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
                place["image"] = res.json()["results"][0]["urls"]["regular"] if res.status_code==200 and res.json().get("results") else "https://via.placeholder.com/400x250?text=No+Image"
            except:
                place["image"] = "https://via.placeholder.com/400x250?text=No+Image"

        return jsonify(travel_data)

    except Exception as e:
        return jsonify([{"name": "추천 여행지", "country": "해외",
                         "description": f"⚠ AI 호출 실패: {e}",
                         "image": "https://via.placeholder.com/400x250"}])

# === region 전용: 마지막 선택 도시 정보만 반환 ===
@app.route("/getCityInfo", methods=["POST"])
def get_city_info():
    data = request.get_json()
    city = data.get("city")
    country = data.get("country")

    if not city or not country:
        return jsonify({"error": "city와 country 필수"}), 400

    prompt = f"{city}, {country}에 대한 2~3문장 여행 설명을 JSON-safe하게 작성해줘. 형식: {{\"description\": \"...\"}}"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip().replace("\n", " ").replace("'", '"')

        # JSON 파싱
        match = re.search(r'\{.*"description".*?\}', text)
        description = ""
        if match:
            try:
                description_json = json.loads(match.group(0))
                description = description_json.get("description", "")
            except:
                description = ""

        # Unsplash 이미지
        try:
            res = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": f"{city} {country}", "client_id": unsplash_key, "per_page": 1}
            )
            image_url = res.json()["results"][0]["urls"]["regular"] if res.status_code==200 and res.json().get("results") else "https://via.placeholder.com/400x250?text=No+Image"
        except:
            image_url = "https://via.placeholder.com/400x250?text=No+Image"

        return jsonify({"name": city, "country": country, "description": description, "image": image_url})

    except Exception as e:
        return jsonify({"name": city, "country": country,
                        "description": f"⚠ AI 호출 실패: {e}",
                        "image": "https://via.placeholder.com/400x250"})

if __name__ == "__main__":
    app.run(debug=True)
