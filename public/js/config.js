// 카카오맵 API 키 설정
const CONFIG = {
    // 카카오 JavaScript 키를 여기에 입력하세요
    // https://developers.kakao.com 에서 발급받으세요
    KAKAO_JAVASCRIPT_KEY: 'YOUR_JAVASCRIPT_KEY',

    // 데이터 파일 경로
    DATA_URL: '../data/stores.json',

    // 기본 지도 설정
    DEFAULT_CENTER: {
        lat: 37.5665,  // 서울 시청
        lng: 126.9780
    },
    DEFAULT_ZOOM: 13,

    // 반경 (미터)
    RADIUS: {
        SMALL: 1000,   // 1km
        MEDIUM: 3000,  // 3km
        LARGE: 5000    // 5km
    },

    // 마커 아이콘 색상
    MARKER_COLOR: {
        STORE: '#FF5252',
        USER: '#2196F3'
    }
};

// 카카오맵 SDK가 로드된 후 실행
if (typeof kakao !== 'undefined') {
    kakao.maps.load(() => {
        console.log('카카오맵 SDK 로드 완료');
    });
}
