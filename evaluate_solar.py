"""
CSV 테스트 케이스에 Solar-pro2 (LangGraph) 결과 추가
"""

import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from database import db_manager
from agents.sql_LG_solar_pro2 import solar_langgraph_agent


def evaluate_test_cases(input_csv: str, output_csv: str):
    """
    테스트 케이스 실행 및 결과 저장
    
    Args:
        input_csv: 입력 CSV 파일 경로
        output_csv: 출력 CSV 파일 경로
    """
    
    # 설정 검증 및 Agent 초기화
    settings.validate()
    solar_langgraph_agent.initialize()
    db = db_manager.get_db()
    
    # CSV 읽기
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)
    
    results = []
    
    print(f"\n총 {len(test_cases)}개 테스트 케이스 실행 중...\n")
    
    for i, case in enumerate(test_cases, 1):
        question = case['input']
        expected_query = case['query']
        expected_label = case['label']
        
        print(f"[{i}/{len(test_cases)}] {question[:50]}...")
        
        try:
            # Solar-pro2 (LangGraph)로 쿼리 생성
            result = solar_langgraph_agent.query(question)
            
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
        
        # 정답 비교
        is_correct = False
        if 'ERROR' not in generated_answer:
            try:
                # 숫자로 변환해서 비교
                expected_val = float(expected_label)
                generated_val = float(generated_answer)
                # 오차 허용 (소수점 6자리까지)
                is_correct = abs(expected_val - generated_val) < 0.000001
            except:
                # 문자열 비교
                is_correct = str(generated_answer).strip() == str(expected_label).strip()
        
        # 결과 저장
        results.append({
            'input': question,
            'expected_query': expected_query,
            'generated_query': generated_query,
            'expected_label': expected_label,
            'generated_answer': generated_answer,
            'is_correct': 'O' if is_correct else 'X'
        })
        
        print(f"   생성 쿼리: {generated_query[:80]}...")
        print(f"   생성 답변: {generated_answer[:80]}...")
        print()
    
    # CSV로 저장
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['input', 'expected_query', 'generated_query', 
                     'expected_label', 'generated_answer', 'is_correct']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✅ 결과 저장 완료: {output_csv}")
    
    # 간단한 통계
    success_count = sum(1 for r in results if 'ERROR' not in r['generated_query'])
    correct_count = sum(1 for r in results if r['is_correct'] == 'O')
    print(f"\n📊 통계:")
    print(f"   총 테스트: {len(results)}개")
    print(f"   쿼리 생성 성공: {success_count}개")
    print(f"   정답 일치: {correct_count}개")
    print(f"   정확도: {correct_count / len(results) * 100:.1f}%")


if __name__ == "__main__":
    input_file = "population_test_lv3_v1.1.csv"
    output_file = "population_test_results_solar.csv"
    
    evaluate_test_cases(input_file, output_file)
