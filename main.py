from agent import VoiceRecruiterAgent

agent = VoiceRecruiterAgent()
result = agent.run()

# Print final interview summary
print("\n--- Final Interview Summary ---")
print(f"Candidate Score: {result.get('candidate_score', 0)}")
print("\nInterview Log:")
for i, entry in enumerate(result.get('interview_log', []), 1):
    print(f"\nQuestion {i}: {entry['question']}")
    print(f"Answer: {entry['answer']}")
    print(f"Evaluation: {entry['evaluation']}")