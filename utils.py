import os

def read_job_description(file_path='job_description.txt'):
    """
    Read job description from a text file.
    
    Args:
        file_path (str): Path to the job description file
    
    Returns:
        str: Contents of the job description file
    """
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Job description file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading job description: {e}")
        return ""

def validate_job_description(job_description):
    """
    Validate the job description to ensure it's not empty.
    
    Args:
        job_description (str): Job description text
    
    Returns:
        bool: Whether the job description is valid
    """
    return bool(job_description and len(job_description.split()) > 10)