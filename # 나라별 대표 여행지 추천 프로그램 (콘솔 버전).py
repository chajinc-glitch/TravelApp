# 나라별 대표 여행지 추천 프로그램 (콘솔 버전)

# 나라별 여행지 데이터
destinations = {
    "한국": [
        "서울: 경복궁, 명동, 홍대",
        "부산: 해운대, 광안리, 자갈치 시장",
        "제주: 성산일출봉, 한라산, 협재해수욕장"
    ],
    "일본": [
        "도쿄: 신주쿠, 아사쿠사, 시부야",
        "오사카: 유니버설 스튜디오, 도톤보리",
        "교토: 기요미즈데라, 금각사"
    ],
    "프랑스": [
        "파리: 에펠탑, 루브르 박물관, 몽마르트",
        "니스: 프로방스, 해변",
        "루앙: 고딕 성당"
    ]
}

def recommend_country():
    print("=== 나라별 대표 여행지 추천 프로그램 ===")
    print("추천 받을 나라를 선택하세요:")

    # 반복문을 이용해 나라 목록 출력
    for country in destinations.keys():
        print(f"- {country}")

    # 사용자 입력
    country = input("나라 입력: ").strip()

    # 선택한 나라의 여행지 출력
    if country in destinations:
        print(f"\n{country} 대표 여행지:")
        for place in destinations[country]:
            print(f"- {place}")
    else:
        print("죄송합니다. 해당 나라 정보가 없습니다.")

# 프로그램 실행
if __name__ == "__main__":
    recommend_country()