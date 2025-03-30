from agent import VoiceRecruiterAgent
from meeting_utils import schedule_google_meet
import time

def main():
    # Schedule a Google Meet interview
    print("Setting up interview session...")
    meet_link = schedule_google_meet(
        summary="AI Recruiter Interview Session",
        description="Automated interview session with AI Recruiter",
        attendee_emails=["candidate@example.com"],  # Replace with actual email
        duration_minutes=30
    )
    
    if meet_link:
        print(f"Interview will begin shortly. Join the meeting at: {meet_link}")
        print("Starting interview in 10 seconds...")
        time.sleep(10)  # Give time to join the meeting
    else:
        print("Could not schedule meeting. Continuing with local interview...")
    
    # Initialize and run the recruiter agent
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

if __name__ == "__main__":
    main()