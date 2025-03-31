from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
import os
import pickle
import time
import webbrowser
import subprocess
import platform

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_credentials():
    """Get valid user credentials from storage or user authorization."""
    creds = None
    token_file = 'token.pickle'
    
    # Load credentials from file if it exists
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def schedule_google_meet(summary, description, attendee_emails, duration_minutes=30):
    """
    Schedule a Google Meet and return the meeting link
    
    Args:
        summary (str): Meeting title
        description (str): Meeting description
        attendee_emails (list): List of email addresses to invite
        duration_minutes (int): Meeting duration in minutes
    
    Returns:
        str: Google Meet link
    """
    try:
        # Get credentials and build service
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        
        # Set meeting time (start immediately)
        start_time = datetime.utcnow() + timedelta(minutes=1)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Format times for Google Calendar API
        start_time_str = start_time.isoformat() + 'Z'
        end_time_str = end_time.isoformat() + 'Z'
        
        # Create attendee list
        attendees = [{'email': email} for email in attendee_emails]
        
        # Create event with Google Meet conference
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time_str,
            },
            'end': {
                'dateTime': end_time_str,
            },
            'attendees': attendees,
            'conferenceData': {
                'createRequest': {
                    'requestId': f'interview-{int(datetime.now().timestamp())}'
                }
            }
        }
        
        # Create the event with conferenceDataVersion=1 to include Meet link
        event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        # Extract Google Meet link
        meet_link = ''
        for entry_point in event.get('conferenceData', {}).get('entryPoints', []):
            if entry_point.get('entryPointType') == 'video':
                meet_link = entry_point.get('uri', '')
                break
        
        print(f"Meeting created: {summary}")
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Google Meet link: {meet_link}")
        
        return meet_link
        
    except Exception as e:
        print(f"Error scheduling meeting: {e}")
        return None

def join_google_meet(meet_link):
    """
    Automatically open and join a Google Meet session.
    
    This function will open the Google Meet link in the default browser
    and help simulate the AI agent "joining" the meeting.
    
    Args:
        meet_link (str): The Google Meet URL to join
        
    Returns:
        bool: True if the meeting was opened, False otherwise
    """
    try:
        # Open the meeting in the default browser
        webbrowser.open(meet_link)
        
        # Delay to allow browser to load
        time.sleep(3)
        
        # Simulate joining the meeting (click join button via keyboard shortcuts)
        # This is a simplified approach - more sophisticated browser automation 
        # would require Selenium or similar tools
        
        # Send keyboard shortcut to join meeting (different per OS)
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # Using AppleScript to simulate keyboard shortcuts
            subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "j" using {command down}'])
        elif system == "Windows":
            # Using AutoHotkey or similar would be more reliable
            subprocess.run(["powershell", "-command", "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^j')"])
        elif system == "Linux":
            # Using xdotool for Linux
            subprocess.run(["xdotool", "key", "ctrl+j"])
        
        print("Attempting to join meeting automatically...")
        return True
        
    except Exception as e:
        print(f"Error joining meeting: {e}")
        print("Please join the meeting manually using the link")
        return False