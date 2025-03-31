import streamlit as st
import time
import os
from agent import VoiceRecruiterAgent
from meeting_utils import schedule_google_meet, join_google_meet
from config import AGENT_VOICE

def main():
    st.set_page_config(page_title="AI Recruiter", page_icon="🤖", layout="wide")
    st.title("AI Recruiter Interview Agent")
    st.write("Upload a job description or enter it manually, then start the interview process.")

    # Sidebar for configuration
    st.sidebar.header("Settings")
    voice_option = st.sidebar.selectbox(
        "Agent Voice",
        ["nova", "alloy", "echo", "fable", "onyx", "shimmer"],
        index=0
    )
    
    interview_duration = st.sidebar.slider(
        "Interview Duration (minutes)",
        min_value=15,
        max_value=60,
        value=30,
        step=5
    )
    
    # Main content area
    tab1, tab2 = st.tabs(["Job Description", "Interview"])
    
    with tab1:
        # Option to upload file or enter text
        job_desc_option = st.radio(
            "Job Description Source",
            ["Upload File", "Enter Text", "Use Default"]
        )
        
        job_description = ""
        
        if job_desc_option == "Upload File":
            uploaded_file = st.file_uploader("Upload Job Description", type=['txt'])
            if uploaded_file:
                job_description = uploaded_file.getvalue().decode("utf-8")
                st.text_area("Job Description Preview", job_description, height=300, disabled=True)
        
        elif job_desc_option == "Enter Text":
            job_description = st.text_area("Enter Job Description", height=300)
        
        else:  # Use Default
            if os.path.exists("job_description.txt"):
                with open("job_description.txt", "r") as f:
                    job_description = f.read()
                st.text_area("Default Job Description", job_description, height=300, disabled=True)
            else:
                st.error("Default job description file not found.")
        
        # Save to file option
        if job_description and job_desc_option != "Use Default":
            if st.button("Save as Default"):
                with open("job_description.txt", "w") as f:
                    f.write(job_description)
                st.success("Job description saved as default!")
    
    with tab2:
        # Email input for meeting invitation
        candidate_email = st.text_input("Candidate Email", value="candidate@example.com")
        
        # Start interview button
        start_col, join_col = st.columns(2)
        
        with start_col:
            start_button = st.button("Schedule & Start Interview", disabled=not job_description)
        
        # Interview process
        if start_button and job_description:
            # Create a placeholder for dynamic content
            interview_status = st.empty()
            interview_log = st.container()
            
            # Step 1: Schedule the meeting
            interview_status.info("Scheduling the meeting...")
            meet_link = schedule_google_meet(
                summary="AI Recruiter Interview Session",
                description="Automated interview session with AI Recruiter",
                attendee_emails=[candidate_email],
                duration_minutes=interview_duration
            )
            
            if meet_link:
                # Show the meeting link
                with join_col:
                    st.success("Meeting scheduled!")
                    st.markdown(f"[Join Meeting]({meet_link})")
                
                # Step 2: Join the meeting
                interview_status.info("Joining the meeting... Please join using the link above.")
                join_result = join_google_meet(meet_link)
                
                if join_result:
                    interview_status.success("Connected to meeting!")
                    
                    # Step 3: Start the interview
                    interview_status.info("Starting the interview process...")
                    
                    # Initialize the agent with the selected voice
                    agent = VoiceRecruiterAgent(in_meeting=True)
                    
                    # Create a progress bar
                    progress = st.progress(0)
                    
                    # Run the interview in stages
                    try:
                        # Run the interview
                        with st.spinner("Interview in progress..."):
                            result = agent.run(job_description=job_description)
                            
                            # Update progress to complete
                            progress.progress(100)
                            
                            # Display results
                            interview_status.success("Interview Complete!")
                            
                            # Display the summary
                            st.header("Interview Summary")
                            st.write(result.get("current_summary", "No summary available."))
                            
                            # Display detailed log
                            st.subheader("Interview Log")
                            for i, entry in enumerate(result.get('interview_log', [])):
                                with st.expander(f"Question {i+1}: {entry['question']}"):
                                    st.write(f"**Answer:** {entry['answer']}")
                                    st.write(f"**Assessment:** {entry.get('evaluation', 'No evaluation')}")
                                    if entry.get('follow_up'):
                                        st.write(f"**Follow-up:** {entry['follow_up']}")
                            
                            # Show the score
                            score = result.get('candidate_score', 0)
                            st.metric("Candidate Score", f"{score:.1f}/10")
                            
                    except Exception as e:
                        interview_status.error(f"Error during interview: {e}")
                        st.exception(e)
                else:
                    interview_status.warning("Could not automatically join the meeting. Please join manually.")
            else:
                interview_status.error("Failed to schedule meeting. Check your Google credentials and try again.")
                
                # Offer to run without meeting
                if st.button("Run Interview Locally (No Meeting)"):
                    try:
                        agent = VoiceRecruiterAgent(in_meeting=False)
                        result = agent.run(job_description=job_description)
                        
                        # Display results
                        st.success("Local interview complete!")
                        st.write(result.get("current_summary", "No summary available."))
                    except Exception as e:
                        st.error(f"Error during local interview: {e}")

if __name__ == '__main__':
    main()