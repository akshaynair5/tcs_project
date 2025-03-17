import subprocess
import re

def clean_response(response):
    cleaned_text = re.sub(r'<.*?>', '', response)
    return cleaned_text

def generate_response(question):
    try:
        result = subprocess.run(
            ['ollama', 'run', 'deepseek-r1:1.5b', question],
            capture_output=True,
            text=False,
            check=True
        )
        raw_output = result.stdout.decode('utf-8')
        return clean_response(raw_output)
    except subprocess.CalledProcessError as e:
        return f"Command failed with error: {e.stderr}"
    except FileNotFoundError:
        return "Error: 'ollama' command not found. Is it installed?"
    except Exception as e:
        return f"Error: {str(e)}"
