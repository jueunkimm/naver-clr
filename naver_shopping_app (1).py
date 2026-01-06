import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# 페이지 설정
st.set_page_config(
    page_title="네이버 쇼핑 세탁기 비교",
    page_icon="🧺",
    layout="wide"
)

# 세션 스테이트 초기화
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_products' not in st.session_state:
    st.session_state.selected_products = []

def search_naver_shopping(query, client_id, client_secret, display=100):
    """네이버 쇼핑 API로 검색"""
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": query,
        "display": display,
        "sort": "sim"  # sim: 정확도순, date: 날짜순, asc: 가격오름차순, dsc: 가격내림차순
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 오류: {str(e)}")
        return None

def clean_html_tags(text):
    """HTML 태그 제거"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def format_price(price):
    """가격 포맷팅"""
    try:
        return f"{int(price):,}원"
    except:
        return price

# 타이틀
st.title("🧺 네이버 쇼핑 세탁기 비교 프로그램")
st.markdown("### 네이버 쇼핑 API를 활용한 실시간 가격 비교")
st.markdown("---")

# 기본 API 설정 (자동으로 설정됨)
DEFAULT_CLIENT_ID = "pd94lBRrTSMumqSi9QYe"
DEFAULT_CLIENT_SECRET = "sMmdrZWOEr"

# 세션 스테이트에 API 키 초기화
if 'client_id' not in st.session_state:
    st.session_state.client_id = DEFAULT_CLIENT_ID
if 'client_secret' not in st.session_state:
    st.session_state.client_secret = DEFAULT_CLIENT_SECRET

# 사이드바 - API 설정
with st.sidebar:
    st.header("🔑 네이버 API 설정")
    
    # API 키 자동 설정 안내
    with st.expander("ℹ️ API 키 정보", expanded=False):
        st.markdown("""
        **현재 상태**: ✅ API 키가 자동으로 설정되어 있습니다!
        
        바로 검색을 시작하실 수 있습니다. 
        
        다른 API 키를 사용하시려면 아래에서 변경하세요.
        """)
    
    # API 키 입력 (기본값이 자동으로 설정됨)
    client_id = st.text_input(
        "Client ID", 
        value=st.session_state.client_id,
        type="default", 
        help="네이버 API Client ID (이미 설정되어 있습니다)"
    )
    client_secret = st.text_input(
        "Client Secret", 
        value=st.session_state.client_secret,
        type="password", 
        help="네이버 API Client Secret (이미 설정되어 있습니다)"
    )
    
    # API 키 업데이트
    if client_id != st.session_state.client_id:
        st.session_state.client_id = client_id
    if client_secret != st.session_state.client_secret:
        st.session_state.client_secret = client_secret
    
    st.markdown("---")
    
    st.header("🔍 검색 옵션")
    search_query = st.text_input("검색어", value="16kg 세탁기", help="검색할 제품명을 입력하세요")
    
    sort_option = st.selectbox(
        "정렬 방식",
        ["정확도순", "가격 낮은순", "가격 높은순"],
        help="검색 결과 정렬 방식"
    )
    
    sort_map = {
        "정확도순": "sim",
        "가격 낮은순": "asc",
        "가격 높은순": "dsc"
    }
    
    display_count = st.slider("검색 결과 수", min_value=10, max_value=100, value=50, step=10)
    
    search_button = st.button("🔍 검색 시작", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # 필터 옵션
    st.header("🎯 필터 옵션")
    min_price = st.number_input("최소 가격 (원)", min_value=0, value=0, step=10000)
    max_price = st.number_input("최대 가격 (원)", min_value=0, value=2000000, step=10000)
    
    brand_filter = st.multiselect(
        "브랜드 필터",
        ["LG", "삼성", "대우", "위니아", "하이얼", "샤오미"]
    )

# 메인 영역
# API 키가 자동으로 설정되어 있으므로 바로 사용 가능
if search_button:
    with st.spinner(f"'{search_query}' 검색 중..."):
        result = search_naver_shopping(
            search_query, 
            client_id, 
            client_secret, 
            display_count
        )
        
        if result and 'items' in result:
            st.session_state.search_results = result['items']
            st.success(f"✅ {len(result['items'])}개의 제품을 찾았습니다!")
        else:
            st.error("검색 결과가 없습니다. 검색어를 변경해보세요.")

if st.session_state.search_results:
    # 필터링
    filtered_results = []
    for item in st.session_state.search_results:
        price = int(item.get('lprice', 0))
        title = clean_html_tags(item.get('title', ''))
        
        # 가격 필터
        if price < min_price or (max_price > 0 and price > max_price):
            continue
        
        # 브랜드 필터
        if brand_filter:
            if not any(brand in title for brand in brand_filter):
                continue
        
        filtered_results.append(item)
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📋 검색 결과", "⭐ 선택한 제품", "📊 비교 분석"])
    
    with tab1:
        st.subheader(f"검색 결과: {len(filtered_results)}개")
        
        if len(filtered_results) == 0:
            st.warning("필터 조건에 맞는 제품이 없습니다. 필터를 조정해보세요.")
        else:
            # 결과를 카드 형식으로 표시
            for idx, item in enumerate(filtered_results[:20]):  # 상위 20개만 표시
                with st.container():
                    col1, col2, col3 = st.columns([1, 4, 1])
                    
                    with col1:
                        # 이미지
                        if item.get('image'):
                            st.image(item['image'], width=100)
                    
                    with col2:
                        # 제품 정보
                        title = clean_html_tags(item['title'])
                        st.markdown(f"**{idx+1}. {title}**")
                        
                        price = format_price(item.get('lprice', 0))
                        st.markdown(f"💰 가격: **{price}**")
                        
                        # 쇼핑몰 정보
                        mall = item.get('mallName', '알 수 없음')
                        st.markdown(f"🏪 판매처: {mall}")
                        
                        # 제품 카테고리
                        category = item.get('category1', '') + ' > ' + item.get('category2', '')
                        if category.strip() != '>':
                            st.markdown(f"📁 카테고리: {category}")
                        
                        # 브랜드 정보
                        brand = item.get('brand', '기타')
                        st.markdown(f"🏷️ 브랜드: {brand}")
                    
                    with col3:
                        # 링크 버튼
                        if item.get('link'):
                            st.markdown(f"[🔗 상품 보기]({item['link']})")
                        
                        # 선택 버튼
                        if st.button(f"⭐ 선택", key=f"select_{idx}"):
                            product_data = {
                                "제품명": title,
                                "가격": int(item.get('lprice', 0)),
                                "브랜드": brand,
                                "판매처": mall,
                                "카테고리": category,
                                "이미지": item.get('image', ''),
                                "링크": item.get('link', ''),
                                "선택일시": datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            
                            # 중복 체크
                            if not any(p['제품명'] == title for p in st.session_state.selected_products):
                                st.session_state.selected_products.append(product_data)
                                st.success(f"✅ '{title[:30]}...' 추가됨!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.warning("이미 선택한 제품입니다!")
                    
                    st.markdown("---")
    
    with tab2:
        st.subheader(f"선택한 제품: {len(st.session_state.selected_products)}개")
        
        if len(st.session_state.selected_products) == 0:
            st.info("'검색 결과' 탭에서 비교할 제품을 선택해주세요!")
        else:
            # 선택한 제품 표시
            for idx, product in enumerate(st.session_state.selected_products):
                with st.container():
                    col1, col2, col3 = st.columns([1, 5, 1])
                    
                    with col1:
                        if product.get('이미지'):
                            st.image(product['이미지'], width=100)
                    
                    with col2:
                        st.markdown(f"**{idx+1}. {product['제품명']}**")
                        st.markdown(f"💰 **{format_price(product['가격'])}**")
                        st.markdown(f"🏪 {product['판매처']} | 🏷️ {product['브랜드']}")
                    
                    with col3:
                        if product.get('링크'):
                            st.markdown(f"[🔗 보기]({product['링크']})")
                        
                        if st.button("🗑️ 삭제", key=f"delete_{idx}"):
                            st.session_state.selected_products.pop(idx)
                            st.rerun()
                    
                    st.markdown("---")
            
            # 전체 삭제
            if st.button("🗑️ 전체 삭제", type="secondary"):
                st.session_state.selected_products = []
                st.rerun()
            
            st.markdown("---")
            
            # 데이터 내보내기
            st.subheader("💾 데이터 내보내기")
            
            df = pd.DataFrame(st.session_state.selected_products)
            
            # CSV 다운로드
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"네이버쇼핑_세탁기비교_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with tab3:
        if len(st.session_state.selected_products) < 2:
            st.info("비교 분석을 위해 2개 이상의 제품을 선택해주세요!")
        else:
            st.subheader("📊 선택 제품 비교 분석")
            
            df = pd.DataFrame(st.session_state.selected_products)
            
            # 가격 통계
            st.markdown("#### 💰 가격 분석")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("최저가", format_price(df['가격'].min()))
            with col2:
                st.metric("최고가", format_price(df['가격'].max()))
            with col3:
                st.metric("평균가", format_price(df['가격'].mean()))
            with col4:
                st.metric("가격차", format_price(df['가격'].max() - df['가격'].min()))
            
            st.markdown("---")
            
            # 가격 순위
            st.markdown("#### 🏆 가격 순위")
            price_df = df.sort_values('가격')[['제품명', '가격', '판매처']].reset_index(drop=True)
            price_df.index = price_df.index + 1
            price_df['가격'] = price_df['가격'].apply(format_price)
            st.dataframe(price_df, use_container_width=True)
            
            st.markdown("---")
            
            # 가격 차트
            st.markdown("#### 📊 가격 비교 차트")
            chart_data = df[['제품명', '가격']].copy()
            chart_data['제품명_short'] = chart_data['제품명'].str[:30] + '...'
            chart_data = chart_data.set_index('제품명_short')
            st.bar_chart(chart_data['가격'])
            
            st.markdown("---")
            
            # 판매처별 분포
            st.markdown("#### 🏪 판매처별 분포")
            mall_counts = df['판매처'].value_counts()
            st.bar_chart(mall_counts)
            
            st.markdown("---")
            
            # 브랜드별 평균 가격
            st.markdown("#### 🏷️ 브랜드별 평균 가격")
            brand_avg = df.groupby('브랜드')['가격'].mean().sort_values(ascending=False)
            st.bar_chart(brand_avg)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🔍 네이버 쇼핑 API를 활용한 실시간 가격 비교 프로그램</p>
    <p>💡 팁: 검색 후 마음에 드는 제품을 선택하여 비교하세요!</p>
    <p>⚖️ 완전 합법적인 방식으로 데이터를 수집합니다</p>
    <p>Made with ❤️ by Claude AI | 2025</p>
</div>
""", unsafe_allow_html=True)
