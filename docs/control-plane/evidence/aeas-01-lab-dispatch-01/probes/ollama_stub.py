"""Local stub of the Ollama /api/chat endpoint (P0.5 adapter-contract probe).

NOT a model. It exists so the served dispatch path can be driven through a real
HTTP adapter call, a real tool execution and a real terminal state, proving the
wire-up and observability without pretending a provider is configured.

Scripted behaviour:
  * first request  -> return one tool_call (filesystem.list, {"path": "."})
  * after a tool result -> return plain text with done_reason "stop"
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8125
CALLS = {"requests": 0}


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *_args):  # keep stdout readable
        pass

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        if not self.path.endswith("/api/chat"):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"unknown path"}')
            return

        CALLS["requests"] += 1
        messages = body.get("messages") or []
        saw_tool_result = any(m.get("role") == "tool" for m in messages)

        if saw_tool_result:
            payload = {
                "model": body.get("model"),
                "message": {
                    "role": "assistant",
                    "content": (
                        "Stub endpoint: the workspace listing was observed. "
                        "No repository change is proposed; this run is read-only."
                    ),
                },
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 12,
                "eval_count": 9,
            }
        else:
            payload = {
                "model": body.get("model"),
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "filesystem.list",
                                "arguments": {"path": "."},
                            }
                        }
                    ],
                },
                "done": True,
                "done_reason": "tool_calls",
                "prompt_eval_count": 8,
                "eval_count": 5,
            }

        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", PORT), Stub).serve_forever()
