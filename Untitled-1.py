import random

# 여행지 데이터 (예시)
travel_data = [
    {"name": "제주도", "region": "한국", "season": "여름", "theme": "힐링", "description": "바다와 자연을 즐길 수 있는 섬"},
    {"name": "부산 해운대", "region": "한국", "season": "여름", "theme": "액티비티", "description": "해수욕과 다양한 해양 스포츠"},
    {"name": "경주", "region": "한국", "season": "봄", "theme": "문화", "description": "신라 천년의 역사가 살아있는 도시"},
    {"name": "서울 명동", "region": "한국", "season": "사계절", "theme": "쇼핑", "description": "쇼핑과 음식이 가득한 거리"},
    {"name": "도쿄", "region": "일본", "season": "사계절", "theme": "쇼핑", "description": "쇼핑과 도시 관광의 중심지"},
    {"name": "오사카 유니버설", "region": "일본", "season": "사계절", "theme": "액티비티", "description": "세계적인 테마파크에서 즐기는 액티비티"},
    {"name": "교토", "region": "일본", "season": "가을", "theme": "문화", "description": "고즈넉한 사찰과 단풍 명소"},
    {"name": "파리", "region": "프랑스", "season": "봄", "theme": "문화", "description": "에펠탑과 루브르 박물관이 있는 낭만의 도시"},
    {"name": "니스", "region": "프랑스", "season": "여름", "theme": "힐링", "description": "지중해 해변에서 즐기는 휴양"},
    {"name": "하와이", "region": "미국", "season": "겨울", "theme": "힐링", "description": "따뜻한 날씨와 해변 휴양지"}
]

def get_user_input():
    season = input("어느 계절에 여행가고 싶나요? (봄/여름/가을/겨울): ").strip()
    theme = input("여행 목적을 고르세요 (힐링/액티비티/문화/쇼핑): ").strip()
    user_type = input("사용자 유형을 선택하세요 (힐링형/액티비티형/문화형): ").strip()
    return season, theme, user_type

def recommend_travel(data, season, theme, user_type):
    results = []

    for t in data:
        score = 0
        if t["season"] == season:
            score += 2
        elif t["season"] == "사계절":
            score += 1

        if t["theme"] == theme:
            score += 3

        if user_type.lower() in t["theme"].lower():
            score += 2

        if score > 0:
            results.append((score, t))

    results.sort(reverse=True, key=lambda x: x[0])
    top_results = [r[1] for r in results[:3]]
    random.shuffle(top_results)
    return top_results

def print_results(results, season, theme):
    if results:
        print(f"\n[{season} / {theme}] 조건에 맞는 추천 여행지:")
        for r in results:
            print(f"- {r['name']} ({r['region']}) → {r['description']}")
    else:
        print(f"\n죄송합니다. [{season} / {theme}] 조건에 맞는 여행지가 없습니다.")

if __name__ == "__main__":
    season, theme, user_type = get_user_input()
    recs = recommend_travel(travel_data, season, theme, user_type)
    print_results(recs, season, theme)