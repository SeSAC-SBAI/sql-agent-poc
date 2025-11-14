"""
CSV 테스트 케이스에 LangGraph Agent 결과 추가
"""

import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from agents.langgraph_agent import langgraph_agent_manager
from database import db_manager


def get_model_name():
    """Agent에서 사용 중인 모델명 추출"""
    try:
        # Agent 초기화 후 모델명 가져오기
        if langgraph_agent_manager.llm is None:
            langgraph_agent_manager.initialize()
        
        model = langgraph_agent_manager.llm.model
        # 파일명에 사용할 수 있도록 정리
        model_name = model.replace(".", "_").replace("-", "_")
        return model_name
    except:
        return "unknown"


def evaluate_test_cases(input_csv: str):
    """
    테스트 케이스 실행 및 결과 저장
    
    Args:
        input_csv: 입력 CSV 파일 경로
    """
    
    # 설정 검증 및 Agent 초기화
    settings.validate()
    langgraph_agent_manager.initialize()
    db = db_manager.get_db()
    
    # 모델명 추출
    model_name = get_model_name()
    output_csv = f"result_lv3_{model_name}.csv"
    
    print(f"\n사용 모델: {model_name}")
    print(f"결과 파일: {output_csv}\n")
    
    # CSV 읽기
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)
    
    results = []
    
    print(f"총 {len(test_cases)}개 테스트 케이스 실행 중...\n")
    
    for i, case in enumerate(test_cases, 1):
        question = case['input']
        expected_query = case['query']
        expected_label = case['label']
        
        print(f"[{i}/{len(test_cases)}] {question[:50]}...")
        
        try:
            # LangGraph Agent로 쿼리 생성
            result = langgraph_agent_manager.query(question)
            
            if result['success']:
                generated_query = result.get('sql_queries', [''])[0] if result.get('sql_queries') else ''
                
                # 생성된 쿼리 실행
                try:
                    sql_result = db.run(generated_query)
                    generated_answer = str(sql_result).strip('[]()').strip()
                except Exception as e:
                    generated_answer = f"ERROR: {str(e)}"
                    
            else:
                generated_query = "ERROR"
                generated_answer = result.get('error', 'Unknown error')
            
        except Exception as e:
            generated_query = "ERROR"
            generated_answer = str(e)
        
        # 결과 저장
        results.append({
            'input': question,
            'expected_query': expected_query,
            'generated_query': generated_query,
            'expected_label': expected_label,
            'generated_answer': generated_answer
        })
        
        print(f"   생성 쿼리: {generated_query[:80]}...")
        print(f"   생성 답변: {generated_answer[:80]}...")
        print()
    
    # CSV로 저장
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['input', 'expected_query', 'generated_query', 
                     'expected_label', 'generated_answer']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✅ 결과 저장 완료: {output_csv}")
    
    # 간단한 통계
    success_count = sum(1 for r in results if 'ERROR' not in r['generated_query'])
    print(f"\n📊 통계:")
    print(f"   총 테스트: {len(results)}개")
    print(f"   성공: {success_count}개")
    print(f"   실패: {len(results) - success_count}개")


if __name__ == "__main__":
    input_file = "population_test_lv3_v1.1.csv"
    evaluate_test_cases(input_file)
