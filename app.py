import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
import json
import re
from amadeus import Client as AmadeusClient, ResponseError
from dotenv import load_dotenv

app = Flask(__name__)

# ==============================
# 🔹 환경 변수
# ==============================
load_dotenv()  # .env 파일 로드

gemini_key = os.getenv("GEMINI_API_KEY")
unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
amadeus_client_id = os.getenv("AMADEUS_CLIENT_ID")
amadeus_client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

if not gemini_key or not unsplash_key:
    raise ValueError("❌ GEMINI_API_KEY 또는 UNSPLASH_ACCESS_KEY가 설정되지 않았습니다!")
if not amadeus_client_id or not amadeus_client_secret:
    raise ValueError("❌ Amadeus API 키가 설정되지 않았습니다!")

# Gemini API 설정
genai.configure(api_key=gemini_key)

# Amadeus 클라이언트 설정
amadeus = AmadeusClient(
    client_id=amadeus_client_id,
    client_secret=amadeus_client_secret
)

# ==============================
# 🔹 기본 페이지
# ==============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/theme")
def theme():
    return render_template("theme.html")

@app.route("/region")
def region():
    return render_template("region.html")

# ==============================
# 🔹 ✈ 항공 페이지 (air.html)
# ==============================
@app.route("/flight")
def flight():
    return render_template("air.html")  # templates/air.html 필요

# ==============================
# 🔹 AI 여행지 추천 API
# ==============================
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    theme = data.get("theme")
    continent = data.get("continent")
    subregion = data.get("subregion")
    country = data.get("country")

    prompt_parts = []
    if theme: prompt_parts.append(f"{theme} 테마")
    if continent: prompt_parts.append(f"대륙: {continent}")
    if subregion: prompt_parts.append(f"하위 지역: {subregion}")
    if country: prompt_parts.append(f"국가: {country}")

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
                place["image"] = (
                    res.json()["results"][0]["urls"]["regular"]
                    if res.status_code == 200 and res.json().get("results")
                    else "https://via.placeholder.com/400x250?text=No+Image"
                )
            except:
                place["image"] = "https://via.placeholder.com/400x250?text=No+Image"

        return jsonify(travel_data)

    except Exception as e:
        return jsonify([{
            "name": "추천 여행지",
            "country": "해외",
            "description": f"⚠ AI 호출 실패: {e}",
            "image": "https://via.placeholder.com/400x250"
        }])

# ==============================
# 🔹 지역별 도시 상세 설명 API
# ==============================
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
            image_url = (
                res.json()["results"][0]["urls"]["regular"]
                if res.status_code == 200 and res.json().get("results")
                else "https://via.placeholder.com/400x250?text=No+Image"
            )
        except:
            image_url = "https://via.placeholder.com/400x250?text=No+Image"

        return jsonify({
            "name": city,
            "country": country,
            "description": description,
            "image": image_url
        })

    except Exception as e:
        return jsonify({
            "name": city,
            "country": country,
            "description": f"⚠ AI 호출 실패: {e}",
            "image": "https://via.placeholder.com/400x250"
        })

# ==============================
# 🔹 Amadeus API 항공 검색 (air.html용) - 안정화 버전
# ==============================
def get_iata_code(city_name):
    try:
        response = amadeus.reference_data.locations.get(
            keyword=city_name,
            subType="CITY"
        )
        if response.data:
            return response.data[0]['iataCode']
        return None
    except Exception as e:
        print(f"IATA 코드 변환 에러: {e}")
        return None

# ==============================
# 🔹 Amadeus API 항공 검색 (air.html용) - 안정화 버전
# ==============================
CITY_TO_IATA = {
    "서울": "ICN",
    "Seoul": "ICN",
    "도쿄": "TYO",
    "Tokyo": "TYO",
    "뉴욕": "NYC",
    "New York": "NYC",
    "파리": "PAR",
    "Paris": "PAR",
    "로마": "ROM",
    "Rome": "ROM",
    "런던": "LON",
    "London": "LON",
    # 필요하면 계속 추가
}

def get_iata_code(city_name):
    # 1️⃣ 직접 매핑 테이블에서 찾기
    iata = CITY_TO_IATA.get(city_name)
    if iata:
        return iata

    # 2️⃣ Amadeus API로 검색
    try:
        response = amadeus.reference_data.locations.get(
            keyword=city_name,
            subType="CITY"
        )
        if response.data:
            return response.data[0]["iataCode"]
    except Exception as e:
        print(f"IATA 코드 변환 에러: {e}")

    return None

# ==============================
# 🔹 HOTEL SEARCH API (Amadeus 통합)
# ==============================
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
HOTEL_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
AMADEUS_API_KEY = amadeus_client_id
AMADEUS_API_SECRET = amadeus_client_secret

def get_access_token():
    """Amadeus API용 Access Token 발급"""
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }
    try:
        response = requests.post(TOKEN_URL, data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print("❌ 토큰 발급 실패:", response.text)
            return None
    except Exception as e:
        print("❌ 토큰 발급 에러:", e)
        return None

@app.route("/hotel")
def hotel_page():
    return render_template("hotel.html")

@app.route("/api/hotel", methods=["GET"])
def get_hotels():
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "city 파라미터 필요"}), 400

    token = get_access_token()
    if not token:
        return jsonify({"error": "토큰 발급 실패"}), 500

    headers = {"Authorization": f"Bearer {token}"}
    params = {"cityCode": city.upper()}

    try:
        response = requests.get(HOTEL_URL, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({"error": "호텔 API 호출 실패", "message": response.text}), 500

        data = response.json()
        hotels = data.get("data", [])

        results = []
        for h in hotels[:10]:
            results.append({
                "hotelName": h.get("name", "N/A"),
                "hotelId": h.get("hotelId", "N/A"),
                "chainCode": h.get("chainCode", "N/A"),
            })

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"호텔 API 호출 실패: {e}"}), 500

# ==============================
# 🚀 실행
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
