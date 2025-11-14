import json
import os
import sqlite3
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
# ✅ 1. DB 연결 설정
# ========================================
DB_PATH = "/mnt/c/Users/User/Documents/final_project/query/data/population_v1.17.db"

if not os.path.exists(DB_PATH):
    print(f"❌ DB 파일을 찾을 수 없습니다: {DB_PATH}")
    print(f"현재 작업 디렉토리: {os.getcwd()}")
    exit(1)
else:
    print(f"✅ DB 파일 확인: {DB_PATH}")


def execute_query(sql: str):
    """SQL을 실행하고 결과 반환"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # ✅ population_stats 테이블에는 '항목', '단위' 컬럼이 없음
        if "FROM population_stats" in sql:
            import re
            sql = re.sub(r"AND\s*항목\s*=\s*'[^']*'\s*", "", sql)
            sql = re.sub(r"AND\s*단위\s*=\s*'[^']*'\s*", "", sql)
            sql = re.sub(r"WHERE\s*항목\s*=\s*'[^']*'\s*AND", "WHERE ", sql)
            sql = re.sub(r"WHERE\s*단위\s*=\s*'[^']*'\s*AND", "WHERE ", sql)
            sql = re.sub(r"WHERE\s*항목\s*=\s*'[^']*'\s*", "", sql)
            sql = re.sub(r"WHERE\s*단위\s*=\s*'[^']*'\s*", "", sql)

        # ✅ 따옴표 처리 통일 (일부 SQL이 "항목" 식으로 들어오는 경우)
        sql = sql.replace('"', '')

        cursor.execute(sql)
        result = cursor.fetchone()
        conn.close()

        if result:
            return str(result[0])
        return None

    except Exception as e:
        print(f"❌ SQL 실행 실패: {e}")
        print(f"🚨 문제 SQL: {sql}")
        return None





# ========================================
# ✅ 2. 모델이 실제 결과 해석 생성
# ========================================
def generate_interpretation_with_your_model(question: str, query_result: str) -> str:

    prompt = f"""당신은 친절한 통계 상담원입니다.

[사용자 질문]
{question}

[데이터베이스 조회 결과]
{query_result}

위 결과를 바탕으로 사용자 질문에 대한 자연스러운 답변을 3문장 이내로 작성하세요.
- 친절한 공공 서비스 톤
- 출처 표기 권장 (〈주민등록인구통계〉 등)
- 숫자는 천 단위 쉼표 사용

답변:"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


# ========================================
# ✅ 3. Judge 평가 프롬프트
# ========================================
EVAL_PROMPT_TEMPLATE = """[SYSTEM]
너는 통계학 분석가이다. 내부적으로 단계적으로 판단하되, 출력은 JSON만 반환하라.

[USER]
다음 정보를 기준으로 모델 출력물을 평가하라.

[Task Description]
* 태스크 유형: 통계 질의응답
* 출력 방식: 친절한 공공 서비스 톤, 출처 표기 권장

[Input Prompt]
{input_prompt}

[Model Output (평가 대상)]
{model_output}

[Query Result (DB 실행 결과)]
{query_result}

[Gold Label (정답값)]
{gold_label}

[Evaluation Criteria]
1. 정확성/사실성
2. 근거성/정당화
3. 관련성/범위준수
4. 지시 준수
5. 안전/편향
6. 한국어 품질
7. 출처 인용

[Output Format (JSON)]
{{
  "scores": {{
    "accuracy": 1-5,
    "grounding": 1-5,
    "relevance": 1-5,
    "instruction_following": 1-5,
    "safety_bias": 1-5,
    "ko_quality": 1-5,
    "citation_use": 1-5
  }},
  "aggregate": {{
    "mean_score": float,
    "grade": "A|B|C|D|E"
  }},
  "evidence_snippets": ["...", "...", "..."],
  "notes": "한 줄 요약(100자 이내)"
}}
"""


# ========================================
# ✅ 4. 메인 평가 루프
# ========================================
input_path = "population_test_lv2_v1.1.jsonl"
output_path = "evaluation_results_interpretation.jsonl"

results = []

with open(input_path, "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f]

for item in tqdm(data, desc="Evaluating Interpretations"):

    original_query = item["input"]
    gold_query = item["query"]

    # ✅ DB 실행 → 정답값(Gold Label)
    query_result = execute_query(gold_query)
    if query_result is None:
        results.append({
            "input": original_query,
            "gold_query": gold_query,
            "error": "SQL 실행 실패"
        })
        continue

    gold_label = query_result  # ✅ 정답값은 DB 결과로 설정

    # ✅ 모델이 직접 해석 생성
    try:
        model_interpretation = generate_interpretation_with_your_model(
            question=original_query,
            query_result=query_result
        )
    except Exception as e:
        results.append({
            "input": original_query,
            "query_result": query_result,
            "error": f"해석 생성 실패: {str(e)}"
        })
        continue

    # ✅ 평가 프롬프트 생성
    eval_prompt = EVAL_PROMPT_TEMPLATE.format(
        input_prompt=original_query,
        model_output=model_interpretation,
        query_result=query_result,
        gold_label=gold_label
    )

    # ✅ Judge 실행
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "너는 통계학 분석가이다. JSON만 반환하라."},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0.0
        )

        evaluation_output = response.choices[0].message.content.strip()

        # JSON 파싱
        try:
            if "```json" in evaluation_output:
                evaluation_output = evaluation_output.split("```json")[1].split("```")[0].strip()
            elif "```" in evaluation_output:
                evaluation_output = evaluation_output.split("```")[1].split("```")[0].strip()

            evaluation_json = json.loads(evaluation_output)

            if "scores" not in evaluation_json:
                raise ValueError("scores 키가 없음")

        except Exception as err:
            evaluation_json = {
                "raw_output": evaluation_output,
                "parse_error": str(err)
            }

        results.append({
            "input": original_query,
            "gold_query": gold_query,
            "query_result": query_result,
            "gold_label": gold_label,
            "model_interpretation": model_interpretation,
            "evaluation": evaluation_json
        })

    except Exception as e:
        results.append({
            "input": original_query,
            "query_result": query_result,
            "model_interpretation": model_interpretation,
            "error": f"평가 실패: {str(e)}"
        })


# ========================================
# ✅ 5. 결과 저장
# ========================================
with open(output_path, "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"✅ 평가 완료! 결과 저장: {output_path}")

# ========================================
# ✅ 6. 통계 출력
# ========================================
success_count = sum(1 for r in results if "evaluation" in r and "scores" in r.get("evaluation", {}))
print(f"📊 성공적으로 평가된 샘플: {success_count}/{len(results)}")

if success_count > 0:
    avg_score = sum(
        r["evaluation"]["aggregate"]["mean_score"]
        for r in results
        if "evaluation" in r and "aggregate" in r.get("evaluation", {})
    ) / success_count

    print(f"📈 평균 점수: {avg_score:.2f}/5.0")
