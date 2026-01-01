class SessionContext:
    """
    Stores per-user session data and memory references.
    """
    def __init__(self, node_id, model=None):
        self.node_id = node_id
        self.model = model
        self.memory = []  # store session prompts/responses

    def add_to_memory(self, prompt, response):
        self.memory.append({"prompt": prompt, "response": response})

    def get_memory(self):
        return self.memory
