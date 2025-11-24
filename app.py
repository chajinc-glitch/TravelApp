import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
import json
import re
from amadeus import Client as AmadeusClient, ResponseError
from dotenv import load_dotenv

app = Flask(__name__)

@app.route('/kyoto')
def kyoto():
    return render_template('kyoto.html')

@app.route('/sydney')
def sydney():
    return render_template('sydney.html')

@app.route('/santorini')
def santorini():
    return render_template('santorini.html')

@app.route('/paris')
def paris():
    return render_template('paris.html')

@app.route('/bali')
def bali():
    return render_template('bali.html')

@app.route('/newyork')
def newyork():
    return render_template('newyork.html')

@app.route('/rome')
def rome():
    return render_template('rome.html')

@app.route('/iceland')
def iceland():
    return render_template('iceland.html')


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
# 🌟 추가: IATA 항공사 코드 -> 이름 매핑
# Amadeus API에서 carrierCode를 'KE', 'OZ', 'TW' 등으로 반환하므로,
# 이를 사용자 친화적인 이름으로 변환하기 위해 사용됩니다.
# ==============================
CARRIER_CODE_TO_NAME = {
    "KE": "대한항공",
    "OZ": "아시아나항공",
    "TW": "티웨이항공",
    "LJ": "진에어",
    "7C": "제주항공",
    "BX": "에어부산",
    "ZE": "이스타항공",
    "DL": "델타항공",
    "UA": "유나이티드항공",
    "AA": "아메리칸 항공",
    "NH": "ANA (전일본공수)",
    "JL": "JAL (일본항공)",
    "CA": "에어 차이나",
    "MU": "중국 동방 항공",
    "SQ": "싱가포르항공",
    # 필요하면 더 추가하세요.
}


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
# (변경 없음)
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
# (변경 없음)
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
# 🔹 IATA 코드 변환 함수 (기존 유지)
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
# 🔹 항공권 검색 API (air.html용) - 수정됨!
# ==============================
@app.route("/search_flight", methods=["POST"])
def search_flight():
    try:
        data = request.get_json()
        origin = data.get("from")
        destination = data.get("to")
        depart_date = data.get("depart_date")
        return_date = data.get("return_date")

        if not origin or not destination:
            return jsonify({"error": "출발지와 도착지를 입력하세요."}), 400

        # IATA 코드 변환
        from_code = get_iata_code(origin)
        to_code = get_iata_code(destination)
        if not from_code or not to_code:
            return jsonify({"error": "도시명을 IATA 코드로 변환할 수 없습니다."}), 400

        # Amadeus 항공편 검색 API
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=from_code,
            destinationLocationCode=to_code,
            departureDate=depart_date,
            returnDate=return_date,
            adults=1,
            currencyCode="USD",
            max=5
        )

        flights = []
        for offer in response.data:
            price = offer["price"]["total"]
            itineraries = offer["itineraries"][0]["segments"]
            first = itineraries[0]
            last = itineraries[-1]
            carrier_code = first["carrierCode"]
            
            # 🌟 수정된 부분: IATA 코드 -> 항공사 이름 변환
            airline_name = CARRIER_CODE_TO_NAME.get(carrier_code, carrier_code)
            
            flights.append({
                "from": origin, # IATA 코드 대신 원본 도시명을 다시 사용
                "to": destination, # IATA 코드 대신 원본 도시명을 다시 사용
                "departure_time": first["departure"]["at"],
                "arrival_time": last["arrival"]["at"],
                "airline": airline_name, # 🌟 변환된 항공사 이름 사용
                "flight_number": first["number"],
                "price": f"${price}"
            })

        return jsonify(flights)

    except ResponseError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"예외 발생: {e}"}), 500




from flask import Flask, request, jsonify, render_template
import requests

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
# 🚦 교통(Traffic/Transit) 기능 시작
# ==============================

import requests
from flask import Flask, request, jsonify, render_template



# GraphHopper API 키
GRAPHHOPPER_KEY = "c87794e5-7930-458b-965b-1c782e438d7c"

# OTP 서버 URL (자체 설치 기준)
OTP_SERVER_URL = "http://localhost:8080/otp/routers/default/plan"

# ==============================
# 🔹 교통 페이지 라우트
# ==============================
@app.route("/traffic")
def traffic_page():
    return render_template("traffic.html")  # templates/traffic.html 필요

# ==============================
# 🔹 Nominatim 주소 → 위도/경도
# ==============================
def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "FlaskApp"})
        data = resp.json()
        if data:
            return data[0]['lat'], data[0]['lon']
        return None, None
    except:
        return None, None

# ==============================
# 🔹 GraphHopper 경로 탐색 API
# ==============================
@app.route("/api/graphhopper_route", methods=["GET"])
def graphhopper_route():
    start = request.args.get("start")  # 주소 또는 "위도,경도"
    end = request.args.get("end")
    vehicle = request.args.get("vehicle", "car")

    if not start or not end:
        return jsonify({"error": "start와 end 파라미터 필요"}), 400

    # 주소 입력이면 위도/경도로 변환
    if "," not in start:
        lat, lon = geocode_address(start)
        if not lat:
            return jsonify({"error": f"출발지 주소를 찾을 수 없음: {start}"}), 400
        start = f"{lat},{lon}"

    if "," not in end:
        lat, lon = geocode_address(end)
        if not lat:
            return jsonify({"error": f"도착지 주소를 찾을 수 없음: {end}"}), 400
        end = f"{lat},{lon}"

    url = f"https://graphhopper.com/api/1/route?point={start}&point={end}&vehicle={vehicle}&locale=ko&calc_points=true&key={GRAPHHOPPER_KEY}"

    try:
        resp = requests.get(url)
        data = resp.json()
        if "paths" in data:
            path = data["paths"][0]
            return jsonify({
                "distance": path.get("distance"),
                "time": path.get("time"),
                "points": path.get("points")
            })
        return jsonify({"error": "경로를 찾을 수 없음", "details": data}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================
# 🔹 OpenTripPlanner 경로 탐색 API (대중교통)
# ==============================
@app.route("/api/otp_route", methods=["GET"])
def otp_route():
    from_addr = request.args.get("from")  # 주소 또는 "위도,경도"
    to_addr = request.args.get("to")
    date = request.args.get("date")
    time = request.args.get("time")

    if not all([from_addr, to_addr, date, time]):
        return jsonify({"error": "모든 파라미터 필요"}), 400

    # 주소 → 위도/경도 변환
    if "," not in from_addr:
        from_lat, from_lon = geocode_address(from_addr)
    else:
        from_lat, from_lon = map(str, from_addr.split(","))

    if "," not in to_addr:
        to_lat, to_lon = geocode_address(to_addr)
    else:
        to_lat, to_lon = map(str, to_addr.split(","))

    if not all([from_lat, from_lon, to_lat, to_lon]):
        return jsonify({"error": "주소를 위도/경도로 변환할 수 없음"}), 400

    params = {
        "fromPlace": f"{from_lat},{from_lon}",
        "toPlace": f"{to_lat},{to_lon}",
        "mode": "TRANSIT,WALK",
        "date": date,
        "time": time,
        "maxWalkDistance": 1000
    }

    try:
        response = requests.get(OTP_SERVER_URL, params=params)
        if response.status_code != 200:
            return jsonify({"error": "OTP 서버 호출 실패", "status": response.status_code, "text": response.text}), 500
        data = response.json()
        if "plan" in data:
            itineraries = data["plan"].get("itineraries", [])
            results = []
            for itin in itineraries:
                legs = []
                for leg in itin.get("legs", []):
                    legs.append({
                        "mode": leg.get("mode"),
                        "startTime": leg.get("startTime"),
                        "endTime": leg.get("endTime"),
                        "from": leg.get("from", {}).get("name"),
                        "to": leg.get("to", {}).get("name"),
                        "distance": leg.get("distance"),
                        "route": leg.get("route")
                    })
                results.append({
                    "duration": itin.get("duration"),
                    "legs": legs
                })
            return jsonify(results)
        return jsonify({"error": "대중교통 경로를 찾을 수 없음", "details": data}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================
# 🚦 교통 기능 종료
# ==============================

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import google.generativeai as genai
import os, json, re


CORS(app)

# ==============================
# 🔹 API Keys
# ==============================
gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

# ==============================
# 🔹 기본 페이지
# ==============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")


# ==============================
# 🔹 여행 일정 생성 API
# ==============================
@app.route("/api/plan_trip", methods=["POST"])
def plan_trip():
    """
    사용자 입력 JSON 예시:
    {
        "places": ["서울", "부산"],
        "days": 3,
        "budget": 300000
    }
    """

    data = request.get_json()
    places = data.get("places", [])
    days = data.get("days", 1)
    budget = data.get("budget", None)   # 🔥 원화 기반 예산

    if not places:
        return jsonify({"error": "여행지를 하나 이상 입력하세요."}), 400

    # ==============================
    # 🔹 Gemini 프롬프트
    # ==============================
    prompt_places = ", ".join(places)
    prompt = f"""
사용자가 입력한 여행지: {prompt_places}
여행 기간: {days}일
예산: {budget}원

요구사항:
- 각 날마다 여행지 3~4곳 추천
- 점심과 저녁 포함
- 각 활동은 시간 순서대로 정렬
- 예상 소요시간 간단히 포함
- JSON 배열 형식으로 반환
- 문자열은 큰따옴표(") 사용
- 출력 예시:
[
  {{
    "day": 1,
    "schedule": [
      {{"time": "09:00", "activity": "경복궁 방문"}},
      {{"time": "12:30", "activity": "점심 식사"}}
    ]
  }}
]
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        text = response.text.strip().replace("\n", " ").replace("'", '"')
        match = re.search(r'\[.*\]', text, re.DOTALL)
        itinerary = json.loads(match.group(0)) if match else []

        # 🔥 이미지 관련 로직 완전 삭제됨

        return jsonify(itinerary)

    except Exception as e:
        return jsonify([
            {
                "day": 1,
                "schedule": [
                    {
                        "time": "09:00",
                        "activity": "AI 일정 생성 실패"
                    }
                ],
                "error": str(e)
            }
        ])


# ==============================
# 🔹 서버 실행
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
