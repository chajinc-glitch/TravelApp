from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# 예시 데이터
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

    # 간단 필터링
    results = [t for t in travel_data if t['region'] == country and t['theme'] == theme]

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
