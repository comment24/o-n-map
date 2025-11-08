# 온누리 상품권 사용처 지도 프로젝트 설계 문서

## 📋 프로젝트 개요

### 목적
온누리 상품권 사용 가능 가맹점을 **위치 기반으로 빠르게 찾고**, 네이버 지도의 풍부한 정보(리뷰, 사진, 가격)를 활용할 수 있는 웹 서비스 제공

### 핵심 요구사항
- **위치 기반 탐색**: 현재 위치 또는 목적지 중심, 반경(1km/3km/5km) 기반 필터링
- **빠른 필터링**: 정적 데이터를 클라이언트에서 즉시 처리 (업종, 상품권 유형)
- **네이버 연동**: 상세 정보는 네이버 지도로 연결하여 리뷰/사진 확인
- **프론트엔드 전용**: 백엔드 없이 완전 정적 사이트
- **자동 업데이트**: GitHub Actions로 주기적 데이터 갱신
- **무료 배포**: GitHub Pages 호스팅

---

## 🔍 리서치 결과

### 1. 데이터 소스

#### 온누리 상품권 가맹점 데이터
- **제공처**: 공공데이터포털 (data.go.kr)
- **데이터명**: 소상공인시장진흥공단_전국 온누리상품권 가맹점 현황
- **접근 방법**:
  - 파일 다운로드: 로그인 없이 가능
  - Open API: 회원가입 및 활용신청 필요 (REST API, JSON/XML 형식)
- **데이터 항목**:
  - 가맹점명
  - 소속 시장명
  - 소재지 (주소)
  - 취급 품목
  - 상품권 유형 (충전식카드/지류/모바일)
- **URL**: https://www.data.go.kr/data/3060079/fileData.do

### 2. 지도 API

#### 카카오맵 JavaScript API
- **서비스**: Kakao Maps Web API
- **특징**:
  - JavaScript SDK 제공
  - 데스크톱 및 모바일 환경 최적화
  - 한국 지도에 특화된 높은 정확도
  - 마커 클러스터링 라이브러리 제공
- **무료 이용량**:
  - **하루 300,000회** 무료 호출 (앱당)
  - Geocoding API 포함
  - 별도 비용 없이 사용 가능
- **문서**:
  - 가이드: https://apis.map.kakao.com/web/guide/
  - 예제: https://apis.map.kakao.com/web/sample/
- **필요사항**: 카카오 계정 (간단한 가입)
- **장점**:
  - 네이버 클라우드 대비 가입 절차 간단
  - 충분한 무료 한도 (정적 사이트는 서버 호출 없음)
  - 한글 문서 우수

#### 네이버 지도 활용 전략
- **iframe 임베드**: 불가능 (X-Frame-Options 제한)
- **공식 API**: 리뷰/사진 제공 안 함
- **우리의 접근**:
  - 카카오맵으로 온누리 가맹점 위치 표시
  - 마커 클릭 시 네이버 지도 URL로 연결 (새 탭/팝업)
  - 사용자가 네이버에서 리뷰/사진/가격 확인
- **법적 안전성**: 네이버 이용약관 준수

### 3. 자동화 시스템

#### GitHub Actions
- **스케줄링**: Cron 표현식을 통한 주기적 실행
- **워크플로우 위치**: `.github/workflows/*.yml`
- **주요 기능**:
  - 정해진 시간에 자동 실행
  - Python/Node.js 등 스크립트 실행 환경 제공
  - 결과물을 저장소에 자동 커밋
  - `workflow_dispatch`로 수동 실행 가능

#### GitHub Pages
- **호스팅**: 정적 사이트 무료 호스팅
- **배포**: `gh-pages` 브랜치 또는 `/docs` 폴더
- **HTTPS**: 기본 제공
- **커스텀 도메인**: 설정 가능

---

## 🏗️ 시스템 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────┐
│         GitHub Actions (Weekly)                 │
│  ┌───────────────────────────────────────────┐  │
│  │ 1. 공공데이터포털에서 가맹점 데이터 수집    │  │
│  │ 2. 주소 → 좌표 변환 (카카오 Geocoding)    │  │
│  │ 3. 네이버 Place ID 매칭 (선택)            │  │
│  │ 4. JSON 정적 파일 생성                    │  │
│  │ 5. 저장소에 자동 커밋                     │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         GitHub Repository                       │
│  ├── /data                                      │
│  │   ├── stores.json (가맹점 + 좌표 + 네이버URL)│
│  │   └── metadata.json (업데이트 정보)         │
│  ├── /public                                    │
│  │   ├── index.html                            │
│  │   ├── css/styles.css                        │
│  │   └── js/                                   │
│  │       ├── map.js (카카오맵)                 │
│  │       ├── filter.js (위치/업종 필터)        │
│  │       └── config.js                         │
│  └── /.github/workflows                         │
│      └── update-data.yml                        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         GitHub Pages (Static Hosting)           │
│  ┌───────────────────────────────────────────┐  │
│  │  [사용자 브라우저]                         │  │
│  │                                            │  │
│  │  1. stores.json 로드 (1회)                │  │
│  │  2. 현재 위치 / 목적지 입력                │  │
│  │  3. 반경 선택 (1km/3km/5km)               │  │
│  │  4. 클라이언트에서 즉시 필터링             │  │
│  │  5. 카카오맵에 마커 표시                   │  │
│  │  6. 마커 클릭 → Dialog 표시                │  │
│  │  7. "네이버에서 보기" → 새 탭/팝업         │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         네이버 지도/플레이스                     │
│  - 리뷰, 사진, 가격, 영업시간                   │
│  - 길찾기, 예약 등                             │
└─────────────────────────────────────────────────┘
```

### 데이터 플로우

1. **데이터 수집** (GitHub Actions - 주 1회 실행)
   ```
   공공데이터포털 파일 다운로드
        ↓
   가맹점 정보 파싱 (CSV/Excel → pandas)
        ↓
   데이터 정제 (중복 제거, 주소 표준화)
        ↓
   카카오 Geocoding API (주소 → 좌표)
        ↓
   네이버 검색으로 Place ID 찾기 (선택)
        ↓
   JSON 파일 생성 (좌표 + 네이버 URL)
        ↓
   Git 커밋 & 푸시
   ```

2. **사용자 조회** (브라우저 - 모두 클라이언트)
   ```
   페이지 로드 → stores.json 다운로드 (1회)
        ↓
   현재 위치 가져오기 (Geolocation API)
        ↓
   사용자 입력: 반경 선택 (1km/3km/5km)
        ↓
   JavaScript로 거리 계산 & 필터링 (즉시)
        ↓
   업종/상품권 유형 필터 적용
        ↓
   카카오맵에 마커 표시
        ↓
   리스트 업데이트 (거리순 정렬)
        ↓
   마커/리스트 클릭 → Dialog 팝업
        ↓
   "네이버에서 보기" → window.open()
   ```

---

## 🛠️ 기술 스택

### Frontend
- **HTML5**: 기본 구조
- **CSS3**: 스타일링
  - Flexbox/Grid 레이아웃
  - 반응형 디자인 (Mobile First)
  - CSS Variables for 테마
- **Vanilla JavaScript**:
  - 지도 제어 (카카오맵 SDK)
  - 위치 기반 필터링 (Geolocation API)
  - 거리 계산 (Haversine formula)
  - Dialog API for 팝업
- **카카오맵 JavaScript API**: 지도 표시 및 마커

### Data Processing (GitHub Actions)
- **Python 3.x**:
  - 공공데이터 파일 다운로드
  - CSV/Excel → JSON 변환
  - 주소 정제 및 Geocoding
  - 네이버 Place ID 매칭 (선택)
- **필요 라이브러리**:
  - `requests`: HTTP 요청
  - `pandas`: 데이터 처리
  - `openpyxl`: Excel 파일 처리
  - `python-dotenv`: 환경변수 관리

### CI/CD
- **GitHub Actions**:
  - 주기적 데이터 업데이트 (Cron)
  - 수동 실행 (workflow_dispatch)
- **GitHub Pages**: 정적 사이트 호스팅

### 외부 API (모두 무료)
- **공공데이터포털**: 온누리 가맹점 데이터 (파일 다운로드)
- **카카오맵 API**:
  - Maps JavaScript API: 지도 표시
  - Geocoding API: 주소 → 좌표 변환
  - 무료 한도: 하루 300,000회
- **네이버 지도**:
  - 외부 링크로만 활용 (API 사용 안 함)
  - URL: `https://map.naver.com/v5/entry/place/{placeId}`

---

## 📂 프로젝트 구조

```
o-n-map/
├── .github/
│   └── workflows/
│       └── update-data.yml          # 데이터 업데이트 자동화
│
├── scripts/
│   ├── fetch_data.py                # 공공데이터 수집
│   ├── geocode.py                   # 주소 → 좌표 변환
│   └── generate_json.py             # JSON 생성
│
├── data/
│   ├── stores.json                  # 가맹점 정보 (좌표 포함)
│   ├── metadata.json                # 데이터 메타정보
│   └── raw/                         # 원본 데이터 (optional)
│
├── public/ (or docs/)
│   ├── index.html                   # 메인 페이지
│   ├── css/
│   │   └── styles.css               # 스타일시트
│   ├── js/
│   │   ├── map.js                   # 지도 제어
│   │   ├── search.js                # 검색 기능
│   │   └── config.js                # 설정 (API 키 등)
│   └── assets/
│       └── images/                  # 이미지 리소스
│
├── .env.example                     # 환경변수 예시
├── .gitignore
├── README.md
└── SPEC.md                          # 이 문서
```

---

## 🔑 핵심 기능 명세

### 1. 위치 기반 탐색 (최우선 기능)
- **현재 위치 자동 감지**: Geolocation API
- **목적지 검색**: 주소, 역명, 동네명 입력
- **반경 선택**:
  - 1km (도보 권장)
  - 3km (자전거/버스)
  - 5km (자동차)
- **실시간 필터링**: 클라이언트에서 즉시 처리 (0.1초 이내)

### 2. 업종 및 상품권 필터
- **업종 카테고리**:
  - 음식점 (한식/중식/일식/양식/카페 등)
  - 식료품 (마트/슈퍼/과일가게 등)
  - 주유소
  - 기타
- **상품권 유형**: 충전식카드/지류/모바일

### 3. 지도 표시
- **카카오맵**: 선택된 가맹점만 표시
- **마커 클러스터링**: 많은 마커 그룹화
- **마커 클릭**: Dialog 팝업

### 4. Dialog 상세 정보
- **기본 정보**:
  - 가맹점명
  - 주소
  - 거리 (현재 위치 기준)
  - 업종
  - 상품권 유형
- **액션 버튼**:
  - 네이버에서 리뷰/사진 보기 (새 탭)
  - 전화걸기 (모바일)
  - 길찾기 (네이버/카카오 선택)

### 5. 리스트 뷰
- **정렬**: 거리순 (가까운 순)
- **빠른 스크롤**: 가상 스크롤링 (성능 최적화)
- **클릭 시**: 지도 중심 이동 + Dialog 표시

### 6. 사용자 경험
- **반응형 디자인**: 모바일 우선 (Mobile First)
- **빠른 로딩**:
  - JSON 압축 (gzip)
  - Progressive loading
- **에러 핸들링**:
  - 위치 권한 거부 시 안내
  - 데이터 로드 실패 시 재시도
- **오프라인 대응**: Service Worker (PWA, 선택사항)

---

## 🔄 데이터 업데이트 프로세스

### GitHub Actions 워크플로우

```yaml
name: Update Store Data

on:
  schedule:
    - cron: '0 2 * * 0'  # 매주 일요일 오전 2시 (KST 11시)
  workflow_dispatch:      # 수동 실행 가능

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
      - name: Setup Python
      - name: Install dependencies
      - name: Fetch data from public API
      - name: Geocode addresses
      - name: Generate JSON files
      - name: Commit and push changes
```

### 데이터 처리 단계

1. **원본 데이터 수집**
   - 공공데이터포털 API 호출 또는 파일 다운로드
   - CSV/Excel 형식 → Python pandas로 로드

2. **데이터 정제**
   - 중복 제거
   - 필수 필드 검증
   - 주소 표준화

3. **Geocoding**
   - 주소 → 위도/경도 변환
   - NAVER Geocoding API 사용
   - 캐싱으로 API 호출 최소화
   - Rate limiting 준수

4. **JSON 생성**
   ```json
   {
     "lastUpdated": "2025-11-08T00:00:00Z",
     "totalStores": 50000,
     "stores": [
       {
         "id": 1,
         "name": "가맹점명",
         "address": "서울시 강남구...",
         "market": "소속 시장명",
         "category": "취급품목",
         "types": ["card", "paper", "mobile"],
         "lat": 37.1234,
         "lng": 127.5678
       }
     ]
   }
   ```

5. **저장소 업데이트**
   - `data/stores.json` 갱신
   - `data/metadata.json` 갱신 (업데이트 시간, 통계 등)
   - Git commit 및 push

---

## 🔐 보안 및 API 키 관리

### 환경 변수 (GitHub Actions용)
- **KAKAO_REST_API_KEY**: 카카오 REST API 키 (Geocoding용)
  - GitHub Actions에서만 사용
  - Repository Secrets에 저장

### 프론트엔드 API 키
- **KAKAO_JAVASCRIPT_KEY**: 카카오 JavaScript 키
  - HTML에 직접 포함 (공개 키)
  - 카카오 개발자 콘솔에서 도메인 제한 설정
  - GitHub Pages 도메인 등록 필수

### API 키 발급 방법
1. **카카오 개발자 콘솔** (https://developers.kakao.com)
   - 로그인 후 "내 애플리케이션" 생성
   - "앱 키" 탭에서 JavaScript 키 복사
   - "플랫폼" 탭에서 웹 플랫폼 추가
   - 사이트 도메인 등록 (예: `https://username.github.io`)

### .gitignore
```
.env
.env.local
*.pyc
__pycache__/
node_modules/
data/raw/
*.xlsx
*.csv
.DS_Store
.vscode/
```

---

## 📊 데이터 스키마

### stores.json
```typescript
interface Store {
  id: number;
  name: string;              // 가맹점명
  address: string;           // 전체 주소
  roadAddress?: string;      // 도로명 주소
  market?: string;           // 소속 시장명
  category: string;          // 업종 (음식점/식료품/주유소 등)
  subCategory?: string;      // 세부 업종 (한식/중식 등)
  types: string[];           // ["card", "paper", "mobile"]
  lat: number;               // 위도
  lng: number;               // 경도
  phone?: string;            // 전화번호
  naverPlaceId?: string;     // 네이버 Place ID (매칭 성공시)
  naverUrl?: string;         // 네이버 지도 URL
}

interface StoreData {
  version: string;           // 데이터 버전
  lastUpdated: string;       // ISO 8601 형식
  totalStores: number;
  stores: Store[];
}
```

**예시**:
```json
{
  "version": "1.0.0",
  "lastUpdated": "2025-11-08T03:00:00Z",
  "totalStores": 45320,
  "stores": [
    {
      "id": 1,
      "name": "맛있는 한식당",
      "address": "서울특별시 강남구 역삼동 123-45",
      "roadAddress": "서울특별시 강남구 테헤란로 456",
      "market": "역삼전통시장",
      "category": "음식점",
      "subCategory": "한식",
      "types": ["card", "paper"],
      "lat": 37.5012,
      "lng": 127.0396,
      "phone": "02-1234-5678",
      "naverPlaceId": "1234567890",
      "naverUrl": "https://map.naver.com/v5/entry/place/1234567890"
    }
  ]
}
```

### metadata.json
```typescript
interface Metadata {
  lastUpdated: string;
  dataSource: string;
  totalStores: number;
  geocodingSuccess: number;  // Geocoding 성공 건수
  geocodingRate: number;     // 성공률 (%)
  naverMatched: number;      // 네이버 Place 매칭 건수
  categories: {
    [key: string]: number;   // 업종별 가맹점 수
  };
  regions: {
    [key: string]: number;   // 지역별 가맹점 수
  };
  types: {
    card: number;
    paper: number;
    mobile: number;
  };
}
```

---

## 🎨 UI/UX 설계

### 레이아웃 (모바일 우선)

#### 모바일 (< 768px)
```
┌─────────────────────────────┐
│  Header                     │
│  📍 [현재위치] [주소검색]    │
│  반경: ◉1km ○3km ○5km       │
│  업종: [전체▼]              │
├─────────────────────────────┤
│                             │
│  카카오맵 (50% 높이)         │
│                             │
├─────────────────────────────┤
│ 🏪 리스트 (거리순)           │
│ ├ 한식당 A (250m)           │
│ ├ 카페 B (420m)             │
│ └ 마트 C (680m)             │
└─────────────────────────────┘

[Dialog 팝업]
┌─────────────────────────────┐
│  🏪 한식당 A            [X] │
│  📍 서울시 강남구...         │
│  📏 250m                    │
│  🏷️ 음식점 > 한식           │
│  💳 충전식, 지류             │
│                             │
│  [네이버에서 리뷰·사진 보기]│
│  [📞 전화] [🗺️ 길찾기]      │
└─────────────────────────────┘
```

#### 데스크톱 (>= 768px)
```
┌────────────────────────────────────────────┐
│  Header                                    │
│  📍 [현재위치] [주소검색]                   │
│  반경: ◉1km ○3km ○5km  업종: [전체▼]       │
├──────────┬─────────────────────────────────┤
│ 리스트   │  카카오맵                        │
│ (30%)    │  (70%)                          │
│          │                                 │
│ 🏪 한식당 A│  📍 마커들                      │
│ 📍 250m  │                                 │
│          │  [Dialog는 지도 위 오버레이]     │
│ 🏪 카페 B │                                 │
│ 📍 420m  │                                 │
└──────────┴─────────────────────────────────┘
```

### 주요 컴포넌트

1. **Header Controls**
   - 위치 입력: 현재 위치 버튼 / 주소 검색창
   - 반경 선택: Radio buttons (1km/3km/5km)
   - 업종 필터: Dropdown (전체/음식점/식료품/주유소)
   - 상품권 유형: Checkboxes (충전식/지류/모바일)

2. **Map (카카오맵)**
   - 사용자 위치 마커 (파란색 원)
   - 가맹점 마커 (빨간색 핀)
   - 마커 클러스터 (많을 때 그룹화)
   - 반경 원형 표시 (선택한 반경)

3. **List Panel**
   - 거리순 정렬
   - 각 항목:
     - 가맹점명
     - 거리
     - 업종 아이콘
   - 클릭 시: 지도 중심 이동 + Dialog

4. **Dialog (HTML dialog 태그)**
   - 가맹점 상세 정보
   - 액션 버튼:
     - 네이버에서 보기 (Primary CTA)
     - 전화걸기
     - 길찾기
   - ESC / X 버튼으로 닫기

---

## 🚀 구현 단계

### Phase 1: 기본 인프라 (1주)
- [x] 리서치 및 설계 문서 작성
- [ ] GitHub 저장소 설정
- [ ] GitHub Actions 워크플로우 작성
- [ ] 데이터 수집 스크립트 개발
- [ ] Geocoding 스크립트 개발

### Phase 2: 프론트엔드 개발 (2주)
- [ ] HTML/CSS 레이아웃 구현
- [ ] 네이버 지도 연동
- [ ] 마커 표시 기능
- [ ] 검색 및 필터 기능
- [ ] 반응형 디자인 적용

### Phase 3: 최적화 및 배포 (1주)
- [ ] 성능 최적화 (마커 클러스터링)
- [ ] 에러 핸들링
- [ ] GitHub Pages 배포
- [ ] 테스트 및 버그 수정

### Phase 4: 고도화 (Optional)
- [ ] PWA 변환 (오프라인 지원)
- [ ] 사용자 즐겨찾기 기능
- [ ] 통계 대시보드
- [ ] 다국어 지원

---

## 📝 고려사항 및 제약

### 기술적 제약
- **Geocoding API 한도**: 네이버 클라우드 무료 이용량 내 사용
  - 전체 데이터를 한 번에 Geocoding 후 캐싱
  - 변경된 데이터만 업데이트
- **GitHub Actions 실행 시간**: 최대 6시간 제한
- **정적 파일 크기**: JSON 파일이 너무 크면 로딩 속도 저하
  - 지역별로 파일 분할 고려
  - 압축 (gzip) 활용

### 데이터 품질
- **주소 정확도**: 공공데이터의 주소 형식이 일관되지 않을 수 있음
- **Geocoding 실패**: 일부 주소는 좌표 변환 실패 가능
  - 실패한 경우 로그 기록 및 수동 보정

### 비용
- **무료 사용 가능**:
  - GitHub Actions: 공개 저장소 무제한
  - GitHub Pages: 무료
  - NAVER Cloud Maps API: 대표 계정 무료 이용량
  - 공공데이터포털: 무료 (일부 API는 신청 필요)

---

## 🔍 참고 자료

### 공식 문서
- **공공데이터포털**: https://www.data.go.kr/data/3060079/fileData.do
- **카카오맵 API**: https://apis.map.kakao.com/web/
  - 가이드: https://apis.map.kakao.com/web/guide/
  - 샘플: https://apis.map.kakao.com/web/sample/
- **GitHub Actions**: https://docs.github.com/en/actions
- **GitHub Pages**: https://docs.github.com/en/pages

### 기술 레퍼런스
- **Geolocation API**: https://developer.mozilla.org/ko/docs/Web/API/Geolocation_API
- **Dialog Element**: https://developer.mozilla.org/ko/docs/Web/HTML/Element/dialog
- **Haversine Formula**: 두 지점 간 거리 계산

### 유사 프로젝트
- 공공 데이터 기반 지도 서비스 예제
- GitHub Actions 정기 크롤링 예제

---

## 📌 다음 단계

### 즉시 실행
1. ✅ 리서치 및 설계 문서 작성 완료
2. ⏭️ **카카오 개발자 계정 생성 및 API 키 발급**
   - https://developers.kakao.com 가입
   - JavaScript 키 발급
3. ⏭️ **공공데이터 파일 다운로드 테스트**
   - 온누리 가맹점 데이터 구조 확인

### Phase 1: 프로토타입 (1-2일)
4. ⏭️ 프로젝트 구조 생성
5. ⏭️ 샘플 데이터로 기본 UI 구현
   - 카카오맵 표시
   - 위치 필터링
   - Dialog 팝업

### Phase 2: 데이터 파이프라인 (2-3일)
6. ⏭️ Python 데이터 수집 스크립트
7. ⏭️ GitHub Actions 워크플로우
8. ⏭️ 실제 데이터로 테스트

### Phase 3: 완성 및 배포 (2-3일)
9. ⏭️ UI/UX 개선
10. ⏭️ 성능 최적화
11. ⏭️ GitHub Pages 배포

---

**문서 버전**: 2.0 (카카오맵 기반)
**작성일**: 2025-11-08
**최종 수정일**: 2025-11-08 (카카오맵으로 설계 변경)
