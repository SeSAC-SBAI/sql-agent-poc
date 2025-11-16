"""
대화형 통계 챗봇 콘솔

사용법:
    python main.py
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from agents.graph import create_stats_chatbot_graph


def print_header():
    """헤더 출력"""
    print("\n" + "=" * 60)
    print("📊 통계 데이터 조회 챗봇")
    print("=" * 60)
    print("명령어:")
    print("  - 질문 입력: 통계 데이터 질문")
    print("  - 'exit' 또는 'quit': 종료")
    print("  - 'clear': 화면 지우기")
    print("=" * 60 + "\n")


def print_separator():
    """구분선"""
    print("\n" + "-" * 60 + "\n")


def clear_screen():
    """화면 지우기"""
    import os

    os.system("clear" if os.name != "nt" else "cls")


def main():
    """메인 함수"""

    # 헤더 출력
    print_header()

    # 그래프 초기화
    print("🔄 챗봇 초기화 중...")
    graph = create_stats_chatbot_graph()
    print("✅ 준비 완료!\n")

    # 대화 ID (세션 관리용)
    thread_id = "console-chat-1"

    # 대화 루프
    while True:
        try:
            # 사용자 입력
            user_input = input("💬 질문: ").strip()

            # 종료 명령
            if user_input.lower() in ["exit", "quit", "종료"]:
                print("\n👋 챗봇을 종료합니다.")
                break

            # 화면 지우기
            if user_input.lower() == "clear":
                clear_screen()
                print_header()
                continue

            # 빈 입력
            if not user_input:
                print("⚠️  질문을 입력해주세요.\n")
                continue

            # 상태 초기화
            state = {
                "user_query": user_input,
                "clarification_count": 0,
                "sql_retry_count": 0,
            }

            # 설정 (세션 관리)
            config = {"configurable": {"thread_id": thread_id}}

            # 그래프 실행
            print("\n🤔 답변 생성 중...\n")
            final_state = graph.invoke(state, config=config)

            # 결과 출력
            print_separator()
            print("📋 답변:")
            print(final_state.get("final_response", "답변을 생성하지 못했습니다."))
            print_separator()

            # 디버그 정보 (선택사항)
            if final_state.get("sql_query"):
                print(f"🔍 실행된 SQL:\n{final_state['sql_query']}\n")

        except KeyboardInterrupt:
            print("\n\n👋 챗봇을 종료합니다.")
            break

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}\n")
            continue


if __name__ == "__main__":
    main()
