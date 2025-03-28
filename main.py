from agent import RecruiterAgent

agent = RecruiterAgent()
result = agent.run()
print("Requirements:\n", result.get('requirements', 'No requirements found'))
print("\nQuestions:\n", result.get('questions', 'No questions generated'))