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
from agents.nodes import format_answer_by_style


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
            
            # 스타일 테스트    
            base_answer = final_state.get("final_response", "")
            user_query = state.get("user_query", "")
            
             # 기본 답변이 있을 때만 스타일 변환 옵션 제공
            if base_answer:
                print("📰 기사, 📄 논문, 📝 블로그 형식으로 다시 보고 싶다면 스타일을 선택하세요.")
                print("    - 기자 기사형: report")
                print("    - 논문 요약형: paper")
                print("    - 블로그 글:  blog")
                style_choice = input("스타일 선택 (report/paper/blog, 그냥 엔터면 건너뜀): ").strip().lower()

                if style_choice in ("report", "paper", "blog"):
                    # 🔹 추가: 사용자가 원하는 방향성을 한 줄 입력 받기
                    style_request = input(
                        "어떤 방향/느낌으로 글을 쓸까요? "
                        "(예: '서울시 관련 칼럼 기사를 쓸거야', '강원도 관련 데이터 통계분석을 통해 연구 논문으로 ', '블로그 후기 느낌으로' 등, 그냥 엔터면 기본 스타일): "
                    ).strip()

                    print("\n🎨 스타일 변환 중...\n")
                    styled_answer = format_answer_by_style(
                        base_answer=base_answer,
                        user_query=user_query,
                        style=style_choice,
                        style_request=style_request or None,  # 🔹 이제 변수 정의됨
                    )

                    print_separator()
                    print(f"📋 스타일({style_choice}) 적용 답변:")
                    print(styled_answer)
                    print_separator()
                
        except KeyboardInterrupt:
            print("\n\n👋 챗봇을 종료합니다.")
            break

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}\n")
            continue


if __name__ == "__main__":
    main()
