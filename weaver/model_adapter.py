import requests

class AIModelAdapter:
    def __init__(self, model_name, api_key=None):
        self.model_name = model_name
        self.api_key = api_key

    def generate(self, prompt, **kwargs):
        if "gemini" in self.model_name.lower():
            return self._gemini_generate(prompt, **kwargs)
        elif "openai" in self.model_name.lower():
            return self._openai_generate(prompt, **kwargs)
        elif "local" in self.model_name.lower():
            return self._local_llm_generate(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")

    def _gemini_generate(self, prompt, **kwargs):
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {"prompt": prompt, **kwargs}
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get("output_text", "")

    def _openai_generate(self, prompt, **kwargs):
        import openai
        openai.api_key = self.api_key
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.choices[0].text

    def _local_llm_generate(self, prompt, **kwargs):
        # Example: integrate local llama.cpp or GPTQ model
        return f"[LOCAL MODEL RESPONSE] {prompt}"
