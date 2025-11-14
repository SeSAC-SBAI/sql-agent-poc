from agents.langgraph_agent import langgraph_agent_manager

if __name__ == "__main__":
    agent = langgraph_agent_manager
    agent.initialize()
    
    while True:
        question = input("\n질문: ")
        if question.lower() in ['quit', 'exit', '종료']:
            break
            
        result = agent.query(question)
        print(f"\n답변: {result['answer']}")