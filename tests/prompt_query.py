# evaluate_queries_solar_v2_FIXED.py
import json
import os
import re
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

MODEL_NAME = "solar-pro2"

# ========================================
# ✅ 1. Gold Constraints 추출 함수
# ========================================
def extract_gold_constraints(sql: str) -> dict:
    """
    SQL에서 제약 조건을 추출하여 딕셔너리로 반환
    """
    constraints = {}
    
    # 행정구역 추출
    region_match = re.search(r"행정구역\s*=\s*'([^']+)'", sql)
    if region_match:
        constraints["region"] = region_match.group(1)
    
    # IN 절로 여러 지역 지정된 경우
    region_in_match = re.search(r"행정구역\s+IN\s*\(([^)]+)\)", sql)
    if region_in_match:
        regions = re.findall(r"'([^']+)'", region_in_match.group(1))
        constraints["region"] = regions
    
    # 년월 추출
    year_match = re.search(r"년월\s*=\s*'([^']+)'", sql)
    if year_match:
        constraints["year"] = year_match.group(1)
    
    # BETWEEN으로 기간 지정된 경우
    between_match = re.search(r"년월\s+BETWEEN\s+'([^']+)'\s+AND\s+'([^']+)'", sql)
    if between_match:
        constraints["year"] = f"{between_match.group(1)}~{between_match.group(2)}"
    
    # 항목 추출 (남자/여자/총인구/세대수)
    metric_match = re.search(r"항목\s*=\s*'([^']+)'", sql)
    if metric_match:
        constraints["metric"] = metric_match.group(1)
    
    # 연령대 추출
    age_match = re.search(r"연령대\s*=\s*'([^']+)'", sql)
    if age_match:
        constraints["age_group"] = age_match.group(1)
    
    # IN 절로 여러 연령대 지정된 경우
    age_in_match = re.search(r"연령대\s+IN\s*\(([^)]+)\)", sql)
    if age_in_match:
        ages = re.findall(r"'([^']+)'", age_in_match.group(1))
        constraints["age_group"] = ages
    
    # 집계 함수 추출
    if "SUM(" in sql:
        constraints["aggregation"] = "SUM"
    elif "AVG(" in sql:
        constraints["aggregation"] = "AVG"
    elif "COUNT(" in sql:
        constraints["aggregation"] = "COUNT"
    elif "MAX(" in sql:
        constraints["aggregation"] = "MAX"
    elif "MIN(" in sql:
        constraints["aggregation"] = "MIN"
    
    # 테이블명 추출
    table_match = re.search(r"FROM\s+(\w+)", sql)
    if table_match:
        constraints["table"] = table_match.group(1)
    
    return constraints


# ========================================
# ✅ 2. 모델 SQL 생성 함수 (예시)
# ========================================
def generate_sql_with_your_model(question: str) -> str:
    """
    여러분 팀의 Text-to-SQL 모델로 SQL 생성
    
    ⚠️ 이 부분은 여러분의 실제 모델로 교체해야 합니다!
    """
    
    # 예시: Solar-Pro2로 SQL 생성 (실제론 여러분 모델 사용)
    prompt = f"""다음 자연어 질문을 SQL로 변환하세요.

테이블:
- population_stats: 세대수 통계 (컬럼: 행정구역, 년월, 항목, 값)
- population_gender_stats: 성별 인구 통계 (컬럼: 행정구역, 년월, 항목, 값)
- population_age_stats: 연령대별 인구 통계 (컬럼: 행정구역, 년월, 연령대, 항목, 값)

질문: {question}

SQL:"""
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": "JSON only. No explanation."},{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    sql = response.choices[0].message.content.strip()
    
    # SQL만 추출 (```sql ... ``` 제거)
    if "```sql" in sql:
        sql = sql.split("```sql")[1].split("```")[0].strip()
    elif "```" in sql:
        sql = sql.split("```")[1].split("```")[0].strip()
    
    return sql


# ========================================
# ✅ 3. 평가 프롬프트 템플릿
# ========================================
PROMPT_TEMPLATE = """[SYSTEM]
너는 Query 생성 평가자이다. 내부적으로 단계적 검토를 하되, 출력은 JSON만 반환하라.

[USER]
원질의(자연어 질의)와 모델이 생성한 Query를 비교·평가하라.

(KOSIS 등 통계 질의 도메인 기준)

[Original_Query]
{original_query}

[Model_Query (평가 대상)]
{model_query}

[Gold_Query (정답 참조)]
{gold_query}

[Gold_Constraints]
{gold_constraints}

[Evaluation Criteria (1–5 each)]
1. 의도 보존: 사용자의 질의 목적이 왜곡되지 않았는가?
2. 정보 보존: 주요 제약(연도, 지역, 성별, 지표 등)이 누락되지 않았는가?
3. 허위 추가 방지: 원질의에 없는 조건이 추가되지 않았는가?
4. 제약 일치도: gold_constraints와 일치 또는 부분 일치하는가?
5. Query 정확성: 실행 결과가 정답과 일치하는가?
6. 안전/편향: 편향·위험 질의 요소가 없는가?

[Output(JSON)]
{{
  "scores": {{
    "intent_preservation": 1-5,
    "info_preservation": 1-5,
    "no_hallucinated_additions": 1-5,
    "constraint_alignment": 1-5,
    "ko_naturalness": 1-5,
    "safety_bias": 1-5
  }},
  "normalized_score": 0.0-1.0,
  "key_diffs": [
    {{"from":"...", "to":"...", "type":"entity|constraint|remove|add"}}
  ],
  "notes": "한 줄 요약(100자 이내)"
}}"""


# ========================================
# ✅ 4. 메인 평가 루프
# ========================================
input_path = "population_test_lv2_v1.1.jsonl"
output_path = "evaluation_results_query_v2.jsonl"

results = []

with open(input_path, "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f]

for item in tqdm(data, desc="Evaluating Queries"):
    original_query = item["input"]      # 사용자 질문
    gold_query = item["query"]          # 정답 SQL
    gold_label = item["label"]          # 정답 결과값
    
    # ✅ 1단계: 모델이 SQL 생성
    try:
        model_query = generate_sql_with_your_model(original_query)
    except Exception as e:
        results.append({
            "input": original_query,
            "gold_query": gold_query,
            "model_query": None,
            "error": f"SQL 생성 실패: {str(e)}"
        })
        continue
    
    # ✅ 2단계: Gold constraints 추출
    gold_constraints = extract_gold_constraints(gold_query)
    
    # ✅ 3단계: 평가 프롬프트 생성
    prompt = PROMPT_TEMPLATE.format(
        original_query=original_query,
        model_query=model_query,
        gold_query=gold_query,
        gold_constraints=json.dumps(gold_constraints, ensure_ascii=False, indent=2)
    )
    
    # ✅ 4단계: LLM Judge로 평가
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "너는 Query 생성 평가자이다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        evaluation_output = response.choices[0].message.content.strip()
        
        # JSON 파싱 시도
        try:
            if "```json" in evaluation_output:
                evaluation_output = evaluation_output.split("```json")[1].split("```")[0].strip()
            elif "```" in evaluation_output:
                evaluation_output = evaluation_output.split("```")[1].split("```")[0].strip()

            evaluation_json = json.loads(evaluation_output)
            if "scores" not in evaluation_json:
                raise ValueError("scores 키가 없음")

        except Exception as e:
            evaluation_json = {"raw_output": evaluation_output, "parse_error": str(e)}
        
        results.append({
            "input": original_query,
            "gold_query": gold_query,
            "model_query": model_query,
            "gold_constraints": gold_constraints,
            "evaluation": evaluation_json
        })
        
    except Exception as e:
        results.append({
            "input": original_query,
            "gold_query": gold_query,
            "model_query": model_query,
            "error": f"평가 실패: {str(e)}"
        })

# ✅ 5단계: 결과 저장
with open(output_path, "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"✅ 평가 완료! 결과 저장: {output_path}")

# ✅ 6단계: 간단한 통계 출력
success_count = sum(1 for r in results if "evaluation" in r and "scores" in r.get("evaluation", {}))
print(f"📊 성공적으로 평가된 샘플: {success_count}/{len(results)}")

if success_count > 0:
    avg_score = sum(
        r["evaluation"]["normalized_score"] 
        for r in results 
        if "evaluation" in r and "normalized_score" in r["evaluation"]
    ) / success_count
    print(f"📈 평균 정규화 점수: {avg_score:.3f}")