from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI
import json

app = Flask(__name__)

# OpenAI 클라이언트 설정
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("환경 변수 OPENAI_API_KEY가 설정되지 않았습니다!")

client = OpenAI(api_key=api_key)

# 예시 데이터 (기존 필터용)
travel_data = [
    {"name": "제주도", "region": "한국", "theme": "힐링", "description": "바다와 자연을 즐길 수 있는 섬"},
    {"name": "부산 해운대", "region": "한국", "theme": "액티비티", "description": "해수욕과 다양한 해양 스포츠"}
]

# HTML 페이지 라우트
@app.route('/')
def index():
    return render_template("index.html")

# 여행지 추천 API
@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    country = data.get('country', '')
    theme = data.get('theme', '')

    # 기존 필터링
    filtered_results = [t for t in travel_data if t['region'] == country and t['theme'] == theme]

    # GPT에게 추천 요청
    prompt = f"""
나라: {country}, 여행 테마: {theme} 조건에 맞는 여행지 3곳을
이름, 지역, 간단한 설명과 함께 JSON 형태로 추천해줘.
예: [{{"name":"서울", "region":"서울", "description":"..."}}]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        gpt_text = response.choices[0].message.content

        # GPT 출력 파싱
        try:
            recommendations = json.loads(gpt_text.replace("'", '"'))
        except:
            # JSON 파싱 실패 시 fallback
            recommendations = [
                {"name": "추천 여행지", "region": country, "description": gpt_text}
            ]

    except Exception as e:
        # GPT 호출 실패 시 fallback
        recommendations = [
            {"name": "추천 여행지", "region": country, "description": f"⚠ GPT 호출 실패: {e}"}
        ]

    # 기존 필터 결과 + GPT 추천 통합
    combined_results = filtered_results + recommendations

    return jsonify(combined_results)

if __name__ == "__main__":
    app.run(debug=True)
