import os, sys, traceback
from dotenv import load_dotenv
load_dotenv()

MODEL = "Qwen/Qwen3-8B"

def step(name, fn):
    try:
        out = fn()
        print(f"[PASS] {name}", f"-> {out}" if out else "")
        return out
    except Exception:
        print(f"[FAIL] {name}")
        traceback.print_exc()
        sys.exit(1)

step("TINKER_API_KEY in .env", lambda: "found" if os.getenv("TINKER_API_KEY") else (_ for _ in ()).throw(RuntimeError("missing")))

import tinker
from tinker import types

def load_tok():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL)
tok = step("Tokenizer download", load_tok)

ids = step("Tokenizer encode", lambda: tok("hello world", add_special_tokens=False)["input_ids"])
sc = step("Tinker ServiceClient", lambda: tinker.ServiceClient())
sampler = step("Create sampling client", lambda: sc.create_sampling_client(base_model=MODEL))

def sample():
    p = types.ModelInput.from_ints(ids)
    r = sampler.sample(prompt=p, num_samples=1,
        sampling_params=types.SamplingParams(max_tokens=10, temperature=0.5)).result()
    return tok.decode(r.sequences[0].tokens)
step("Sample text", sample)
print("\nAll steps passed. Python side is working.")