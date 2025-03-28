from agent import AdvancedRecruiterAgent

agent = AdvancedRecruiterAgent()
result = agent.run()

# Print interview summary
print("\n--- Interview Summary ---")
print("Interview Log:")
for i, entry in enumerate(result.get('interview_log', []), 1):
    print(f"\nQuestion {i}: {entry['question']}")
    print(f"Answer: {entry['answer']}")
    print(f"Evaluation: {entry['evaluation']}")

print(f"\nCandidate Score: {result.get('candidate_score', 0)}")