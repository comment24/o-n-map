// 필터링 관리 모듈
class FilterManager {
    constructor() {
        this.allStores = [];
        this.filteredStores = [];
        this.userLocation = null;
        this.selectedRadius = CONFIG.RADIUS.SMALL;
        this.selectedCategory = 'all';
        this.selectedTypes = ['card', 'paper', 'mobile'];
    }

    /**
     * 전체 가맹점 데이터 설정
     * @param {Array} stores - 가맹점 배열
     */
    setStores(stores) {
        this.allStores = stores;
        console.log(`전체 가맹점 ${stores.length}개 로드 완료`);
    }

    /**
     * 사용자 위치 설정
     * @param {number} lat - 위도
     * @param {number} lng - 경도
     */
    setUserLocation(lat, lng) {
        this.userLocation = { lat, lng };
        this.applyFilters();
    }

    /**
     * 반경 설정
     * @param {number} radius - 반경 (미터)
     */
    setRadius(radius) {
        this.selectedRadius = radius;
        if (this.userLocation) {
            this.applyFilters();
        }
    }

    /**
     * 카테고리 설정
     * @param {string} category - 카테고리
     */
    setCategory(category) {
        this.selectedCategory = category;
        if (this.userLocation) {
            this.applyFilters();
        }
    }

    /**
     * 상품권 유형 설정
     * @param {Array<string>} types - 선택된 유형들
     */
    setTypes(types) {
        this.selectedTypes = types;
        if (this.userLocation) {
            this.applyFilters();
        }
    }

    /**
     * 필터 적용
     */
    applyFilters() {
        if (!this.userLocation) {
            this.filteredStores = [];
            return;
        }

        const startTime = performance.now();

        // 1. 거리 계산 및 반경 필터
        let filtered = this.allStores.map(store => {
            const distance = calculateDistance(
                this.userLocation.lat,
                this.userLocation.lng,
                store.lat,
                store.lng
            );

            return {
                ...store,
                distance: distance
            };
        }).filter(store => store.distance <= this.selectedRadius);

        // 2. 카테고리 필터
        if (this.selectedCategory !== 'all') {
            filtered = filtered.filter(store =>
                store.category === this.selectedCategory
            );
        }

        // 3. 상품권 유형 필터
        if (this.selectedTypes.length > 0) {
            filtered = filtered.filter(store =>
                store.types.some(type => this.selectedTypes.includes(type))
            );
        }

        // 4. 거리순 정렬
        filtered.sort((a, b) => a.distance - b.distance);

        this.filteredStores = filtered;

        const endTime = performance.now();
        console.log(`필터링 완료: ${filtered.length}개 (${(endTime - startTime).toFixed(2)}ms)`);

        return filtered;
    }

    /**
     * 필터링된 가맹점 가져오기
     * @returns {Array}
     */
    getFilteredStores() {
        return this.filteredStores;
    }

    /**
     * 통계 정보 가져오기
     * @returns {Object}
     */
    getStats() {
        return {
            total: this.allStores.length,
            filtered: this.filteredStores.length,
            categories: this.getCategoryStats(),
            types: this.getTypeStats()
        };
    }

    /**
     * 카테고리별 통계
     * @returns {Object}
     */
    getCategoryStats() {
        const stats = {};
        this.filteredStores.forEach(store => {
            const category = store.category || '기타';
            stats[category] = (stats[category] || 0) + 1;
        });
        return stats;
    }

    /**
     * 상품권 유형별 통계
     * @returns {Object}
     */
    getTypeStats() {
        const stats = { card: 0, paper: 0, mobile: 0 };
        this.filteredStores.forEach(store => {
            store.types.forEach(type => {
                if (stats.hasOwnProperty(type)) {
                    stats[type]++;
                }
            });
        });
        return stats;
    }

    /**
     * ID로 가맹점 찾기
     * @param {number} id - 가맹점 ID
     * @returns {Object|null}
     */
    findStoreById(id) {
        return this.allStores.find(store => store.id === id) || null;
    }

    /**
     * 검색어로 가맹점 찾기
     * @param {string} query - 검색어
     * @returns {Array}
     */
    searchStores(query) {
        if (!query || query.trim().length === 0) {
            return this.filteredStores;
        }

        const searchTerm = query.toLowerCase();
        return this.filteredStores.filter(store =>
            store.name.toLowerCase().includes(searchTerm) ||
            store.address.toLowerCase().includes(searchTerm) ||
            (store.market && store.market.toLowerCase().includes(searchTerm))
        );
    }
}

// 전역 인스턴스 생성
const filterManager = new FilterManager();
