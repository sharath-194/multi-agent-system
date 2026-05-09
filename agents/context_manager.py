import json

class ContextManager:
    def __init__(self, max_budget: int = 4000):
        self.max_budget = max_budget
        self.context = {}

    def count_tokens(self, text: str) -> int:
        return len(text.split()) * 2

    def get_remaining_budget(self) -> int:
        current = self.count_tokens(json.dumps(self.context, default=str))
        return self.max_budget - current

    def update(self, key: str, value):
        self.context[key] = value

    def get(self, key: str):
        return self.context.get(key)

    def get_all(self) -> dict:
        return self.context

    def check_budget(self) -> bool:
        return self.get_remaining_budget() > 0

    def summarize_old_context(self):
        if "conversation_history" in self.context:
            history = self.context["conversation_history"]
            if len(history) > 4:
                self.context["conversation_history"] = history[-4:]
                self.context["context_compressed"] = True