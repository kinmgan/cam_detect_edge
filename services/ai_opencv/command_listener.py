# services/ai_opencv/command_listener.py
import redis
import json
import threading

class CommandListener(threading.Thread):
    def __init__(self, ai_wrapper, host='redis', port=6379):
        super().__init__()
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe("ai_commands")
        self.ai_wrapper = ai_wrapper
        self.daemon = True

    def run(self):
        print("Command Listener đang lắng nghe lệnh từ FE...")
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                command = json.loads(message['data'])
                if command.get("action") == "switch_model":
                    new_model = command.get("model_name")
                    print(f"Đang chuyển đổi sang model: {new_model}")
                    self.ai_wrapper.switch_model(new_model)