// 유틸리티 함수들

/**
 * Haversine formula를 사용한 두 지점 간 거리 계산 (미터)
 * @param {number} lat1 - 위도 1
 * @param {number} lng1 - 경도 1
 * @param {number} lat2 - 위도 2
 * @param {number} lng2 - 경도 2
 * @returns {number} 거리 (미터)
 */
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371e3; // 지구 반지름 (미터)
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lng2 - lng1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
}

/**
 * 거리를 읽기 쉬운 형식으로 변환
 * @param {number} meters - 거리 (미터)
 * @returns {string} 형식화된 거리
 */
function formatDistance(meters) {
    if (meters < 1000) {
        return `${Math.round(meters)}m`;
    } else {
        return `${(meters / 1000).toFixed(1)}km`;
    }
}

/**
 * ISO 날짜를 읽기 쉬운 형식으로 변환
 * @param {string} isoDate - ISO 8601 날짜 문자열
 * @returns {string} 형식화된 날짜
 */
function formatDate(isoDate) {
    const date = new Date(isoDate);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * 배열에서 특정 키로 값 추출
 * @param {Array} arr - 배열
 * @param {string} key - 키
 * @returns {Array} 고유 값 배열
 */
function getUniqueValues(arr, key) {
    const values = arr.map(item => item[key]).filter(Boolean);
    return [...new Set(values)];
}

/**
 * 상품권 유형 배열을 읽기 쉬운 형식으로 변환
 * @param {Array<string>} types - 상품권 유형 배열
 * @returns {string} 형식화된 문자열
 */
function formatStoreTypes(types) {
    const typeNames = {
        card: '충전식',
        paper: '지류',
        mobile: '모바일'
    };
    return types.map(t => typeNames[t] || t).join(', ');
}

/**
 * 전화번호 형식 확인
 * @param {string} phone - 전화번호
 * @returns {boolean} 유효성
 */
function isValidPhone(phone) {
    return phone && phone.trim().length > 0;
}

/**
 * 네이버 지도 검색 URL 생성
 * @param {string} name - 가맹점명
 * @param {string} address - 주소
 * @returns {string} URL
 */
function generateNaverSearchUrl(name, address) {
    const query = encodeURIComponent(`${name} ${address}`);
    return `https://map.naver.com/v5/search/${query}`;
}

/**
 * 네이버 Place URL 생성
 * @param {string} placeId - Place ID
 * @returns {string} URL
 */
function generateNaverPlaceUrl(placeId) {
    return `https://map.naver.com/v5/entry/place/${placeId}`;
}

/**
 * 카카오/네이버 길찾기 URL 생성
 * @param {number} lat - 위도
 * @param {number} lng - 경도
 * @param {string} name - 목적지 이름
 * @returns {object} URLs
 */
function generateDirectionsUrls(lat, lng, name) {
    return {
        kakao: `https://map.kakao.com/link/to/${encodeURIComponent(name)},${lat},${lng}`,
        naver: `https://map.naver.com/v5/directions/-/-/-/transit?c=${lng},${lat},15,0,0,0,dh`
    };
}

/**
 * 디바운스 함수
 * @param {Function} func - 실행할 함수
 * @param {number} wait - 대기 시간 (ms)
 * @returns {Function} 디바운스된 함수
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
