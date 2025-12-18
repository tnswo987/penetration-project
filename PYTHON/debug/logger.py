from datetime import datetime

class Logger:
    def __init__(self, filename="log.txt"):
        self.filename = filename
        self.log_index = 1
        
    def log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f"{now} {msg}\n")
    
    def mlog(self, level, source, message):
        """
        format:
        index,YYYY-MM-DD HH:MM:SS,LEVEL,SOURCE,MESSAGE
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{self.log_index},{timestamp},{level},{source},{message}\n"

        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)

        self.log_index += 1