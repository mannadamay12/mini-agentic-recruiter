import streamlit as st
import time
import webbrowser
from agent import VoiceRecruiterAgent
from meeting_utils import schedule_google_meet

def main():
    st.title("AI Recruiter Interview Agent")
    st.write("Enter the job description below and click **Start Interview** to begin.")

    # Input for job description
    job_description = st.text_area("Job Description", height=200)
    
    if st.button("Start Interview") and job_description:
        st.info("Scheduling the meeting...")
        # Schedule a Google Meet interview
        meet_link = schedule_google_meet(
            summary="AI Recruiter Interview Session",
            description="Automated interview session with AI Recruiter",
            attendee_emails=["candidate@example.com"],  # Replace as needed
            duration_minutes=30
        )
        
        if meet_link:
            st.success(f"Meeting scheduled! Please join the meeting at: [Join Meeting]({meet_link})")
            
            # Open the meeting link in the default web browser (simulates agent joining)
            webbrowser.open(meet_link)
            st.info("The agent is joining the meeting. Waiting for candidate to join...")
            
            # Wait for a moment to simulate candidate joining (adjust as necessary)
            time.sleep(10)
            
            # Run the interview
            st.info("Starting the interview...")
            agent = VoiceRecruiterAgent()
            result = agent.run(job_description=job_description)
            
            # Display final summary
            st.success("Interview Complete!")
            st.header("Interview Summary")
            st.write(f"**Candidate Score:** {result.get('candidate_score', 0)}")
            st.subheader("Interview Log")
            for i, entry in enumerate(result.get('interview_log', []), 1):
                st.write(f"**Question {i}:** {entry['question']}")
                st.write(f"**Answer:** {entry['answer']}")
                st.write(f"**Evaluation:** {entry['evaluation']}")
        else:
            st.error("Could not schedule the meeting. Please try again.")

if __name__ == '__main__':
    main()
