import os
import json
from weaver.recursive import RecursiveEngine

# Monkeypatch the LLM to deterministic behavior for this run.
from weaver.agent import call_llm as original_call_llm


def deterministic_stub(provider, prompt):
    # Extract step index from the task embedded in the prompt
    import re
    m = re.search(r"recursive step (\d+)", prompt)
    step = int(m.group(1)) if m else 0
    # produce a minimal file patch intended to be adopted by agent.run
    target = f'weaver/notes/cycle_4_step_{step}.txt'
    content = f'Cycle 4 step {step}: Safe deterministic update.\n'
    return f"--- FILE: {target} ---\n{content}\n"


os.environ['ARKADIA_RECURSIVE_ENABLED'] = 'true'
os.environ['RECURSIVE_DEPTH'] = '4'

# inject the stub into the weaver.agent module at runtime
import weaver.agent as agent
agent.call_llm = deterministic_stub

engine = RecursiveEngine(initial_task='cycle 4 auto update')
engine.set_depth(4)
engine.start()
# Ensure the internal depth state reflects the requested change
engine.depth = 4
report = engine.report()
print(json.dumps(report, indent=2))
