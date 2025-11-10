import chromadb
from chromadb.config import Settings

def setup_embedding_db():
    # ChromaDB 클라이언트 생성
    client = chromadb.PersistentClient(path="./embeding_DB")
    
    # 컬렉션 생성 (이미 있으면 가져옴)
    collection = client.get_or_create_collection(
        name="table_metadata",
        metadata={"description": "Population DB table metadata"}
    )
    
    # 임베딩할 문서들
    documents = [
        "population_age_stats 테이블: 연령대별 인구 통계. 0-4세, 5-9세 등 5세 단위로 나눈 연령대별 남녀 인구수. 30대, 40대, 고령, 청년, 노인 같은 연령 관련 질문에 사용. 컬럼: 행정구역, 년월, 연령대, 항목(총인구수/남자인구수/여자인구수), 값",
        
        "population_gender_stats 테이블: 성별 인구 통계. 지역별 총인구수, 남자인구수, 여자인구수 정보. 전체 인구나 성별 인구 질문에 사용. 연령대 구분 없음. 컬럼: 행정구역, 년월, 항목(총인구수/남자인구수/여자인구수), 값",
        
        "population_stats 테이블: 세대수 통계. 지역별 세대수, 가구수 정보. 세대, 가구 관련 질문에 사용. 컬럼: 행정구역, 년월, 값"
    ]
    
    metadatas = [
        {
            "table_name": "population_age_stats",
            "keywords": "연령,나이,고령,청년,노인,65세이상,30대,40대,5세단위,연령대",
            "columns": "행정구역,년월,연령대,항목,값"
        },
        {
            "table_name": "population_gender_stats",
            "keywords": "총인구수,인구,남자,여자,성별,인구수,사람,거주민",
            "columns": "행정구역,년월,항목,값"
        },
        {
            "table_name": "population_stats",
            "keywords": "세대,세대수,가구,가구수,household",
            "columns": "행정구역,년월,값"
        }
    ]
    
    ids = ["table_0", "table_1", "table_2"]
    
    # 임베딩 추가
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print("✅ ChromaDB 임베딩 완료!")
    print(f"저장 위치: ./embeding_DB")
    print(f"컬렉션: {collection.name}")
    print(f"문서 수: {collection.count()}")
    
    return collection

def search_table(query, n_results=1):
    client = chromadb.PersistentClient(path="./embeding_DB")
    collection = client.get_collection(name="table_metadata")
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    return results

if __name__ == "__main__":
    # 초기 설정
    collection = setup_embedding_db()
    
    # 테스트
    test_queries = [
        "2020년 1월부터 2020년 12월까지 수원시의 세대수 모두 합치면 몇 세대야?"
    ]
    
    print("\n" + "="*60)
    print("테스트 검색")
    print("="*60)
    
    for query in test_queries:
        result = search_table(query)
        table_name = result['metadatas'][0][0]['table_name']
        print(f"\n질문: {query}")
        print(f"→ 선택된 테이블: {table_name}")