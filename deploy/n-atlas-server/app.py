import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama

MODEL_REPO = os.getenv('N_ATLAS_MODEL_REPO', 'QuantFactory/N-ATLaS-GGUF')
MODEL_FILE = os.getenv('N_ATLAS_MODEL_FILE', '')
MODEL_PATH = os.getenv('N_ATLAS_MODEL_PATH', '')
API_KEY = os.getenv('N_ATLAS_API_KEY', '')

app = FastAPI(title='N-ATLaS OpenAI-Compatible Gateway', version='0.1.0')
llm = None

class ChatRequest(BaseModel):
    model: str = 'n-atlas'
    messages: list[dict]
    max_tokens: int | None = 256
    temperature: float | None = 0.2
    top_p: float | None = 0.95
    stream: bool | None = False

def auth(authorization: str | None):
    if API_KEY and authorization != f'Bearer {API_KEY}':
        raise HTTPException(status_code=401, detail='invalid API key')

def load_model():
    global llm
    if llm is not None: return llm
    kwargs = dict(n_ctx=4096, n_threads=max(2, os.cpu_count() or 2), n_gpu_layers=0, verbose=False)
    if MODEL_PATH:
        path = MODEL_PATH
    else:
        from huggingface_hub import hf_hub_download
        if not MODEL_FILE: raise RuntimeError('N_ATLAS_MODEL_FILE must be set when MODEL_PATH is absent')
        path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE)
    llm = Llama(model_path=path, **kwargs)
    return llm

@app.get('/health')
def health(): return {'status':'ok','provider':'n_atlas','model':'n-atlas'}

@app.get('/v1/models')
def models(authorization: str | None = Header(default=None)):
    auth(authorization)
    return {'object':'list','data':[{'id':'n-atlas','object':'model','owned_by':'NCAIR1'}]}

@app.post('/v1/chat/completions')
def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    if req.stream: raise HTTPException(status_code=400, detail='streaming is not enabled in v0.1')
    result = load_model().create_chat_completion(messages=req.messages, max_tokens=req.max_tokens or 256, temperature=req.temperature if req.temperature is not None else 0.2, top_p=req.top_p if req.top_p is not None else 0.95)
    choice = result['choices'][0]
    return {'id':result.get('id','n-atlas-run'),'object':'chat.completion','model':'n-atlas','choices':[{'index':0,'message':{'role':'assistant','content':choice['message'].get('content','')},'finish_reason':choice.get('finish_reason','stop')}],'usage':result.get('usage',{})}
