# 온누리 상품권 사용처 지도

온누리 상품권을 사용할 수 있는 가맹점을 **위치 기반으로 빠르게 찾고**, 네이버 지도의 리뷰와 사진을 확인할 수 있는 웹 서비스입니다.

## ✨ 주요 기능

- 📍 **위치 기반 탐색**: 현재 위치 또는 목적지 중심으로 반경(1km/3km/5km) 내 가맹점 검색
- ⚡ **빠른 필터링**: 클라이언트에서 즉시 처리 (업종, 상품권 유형)
- 🗺️ **카카오맵**: 가맹점 위치 시각화
- 🔗 **네이버 연동**: 상세 정보(리뷰, 사진, 가격)는 네이버 지도로 연결
- 📱 **모바일 최적화**: 반응형 디자인

## 🛠️ 기술 스택

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Map**: 카카오맵 JavaScript API
- **Data**: GitHub Actions + Python
- **Deploy**: GitHub Pages

## 🚀 시작하기

### 필요 사항

1. 카카오 개발자 계정 ([https://developers.kakao.com](https://developers.kakao.com))
2. JavaScript 키 발급

### 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/o-n-map.git
cd o-n-map

# public/js/config.js에 카카오 API 키 설정
# 로컬 서버 실행 (Python)
cd public
python -m http.server 8000

# 브라우저에서 http://localhost:8000 열기
```

### 배포

GitHub Pages로 자동 배포됩니다.

## 📊 데이터 소스

- **온누리 상품권 가맹점**: [공공데이터포털](https://www.data.go.kr/data/3060079/fileData.do)
- **업데이트 주기**: 매주 일요일 자동

## 📝 라이선스

MIT License

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

## 📖 문서

자세한 설계 문서는 [SPEC.md](SPEC.md)를 참조하세요.
