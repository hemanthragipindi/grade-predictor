import urllib.request
import os
import json

def send_notification(title, message, priority="default"):
    """
    Sends notification to multiple channels using built-in libraries:
    1. ntfy.sh (Mobile/Laptop)
    """
    
    # 1. Load settings to get ntfy topic
    SETTINGS_FILE = "settings.json"
    ntfy_topic = None
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                ntfy_topic = data.get("ntfy_topic")
        except:
            pass

    # 2. NTFY.SH (Mobile/Laptop)
    if ntfy_topic:
        try:
            # priority: 5=max, 4=high, 3=default, 2=low, 1=min
            ntfy_prio = "3"
            if priority == "high": ntfy_prio = "4"
            elif priority == "urgent": ntfy_prio = "5"
            elif priority == "low": ntfy_prio = "2"

            url = f"https://ntfy.sh/{ntfy_topic}"
            headers = {
                "Title": title,
                "Priority": ntfy_prio,
                "Tags": "mortar_board,bell"
            }
            
            # Encode headers to avoid encoding issues with urllib
            req = urllib.request.Request(url, data=message.encode('utf-8'), method='POST')
            for k, v in headers.items():
                req.add_header(k, v)
                
            with urllib.request.urlopen(req, timeout=5) as response:
                success = response.status == 200
                with open("notifications.log", "a") as log:
                    log.write(f"[{os.getpid()}] {title} - {'Success' if success else 'Failed'}\n")
                return success
        except Exception as e:
            with open("notifications.log", "a") as log:
                log.write(f"[{os.getpid()}] Error: {e}\n")
            print(f"Error sending ntfy notification: {e}")
    
    return False
