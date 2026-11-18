# shared batched generation helper for small open models on CPU (bf16, left padding)
# models load from $MODELS_DIR/<folder> if present, otherwise from the Hugging Face hub id
import os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
torch.set_num_threads(int(os.environ.get("THREADS", "4")))
MODELS_DIR = os.environ.get("MODELS_DIR", "models")
HF = {
 "qwen2.5-0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
 "qwen2.5-1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
 "llama3.2-1b": "unsloth/Llama-3.2-1B-Instruct",
 "smollm2-1.7b": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
 "gemma2-2b": "unsloth/gemma-2-2b-it",
}
NO_SYSTEM_ROLE = {"gemma2-2b"}

def _path(name):
    local = os.path.join(MODELS_DIR, HF[name].split("/")[-1])
    return local if os.path.isdir(local) else HF[name]

class Gen:
    def __init__(self, name):
        self.name = name
        p = _path(name)
        self.tok = AutoTokenizer.from_pretrained(p)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16)
        self.model.eval()

    def fmt(self, msgs):
        if self.name in NO_SYSTEM_ROLE and msgs and msgs[0]["role"] == "system":
            msgs = [{"role": "user", "content": msgs[0]["content"] + "\n\n" + msgs[1]["content"]}] + msgs[2:]
        return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    @torch.no_grad()
    def generate(self, convs, max_new=128, temperature=0.7, top_p=0.95, bs=16, seed=0):
        texts = [self.fmt(c) for c in convs]
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        outs = [None] * len(texts)
        for bi in range(0, len(order), bs):
            idx = order[bi:bi + bs]
            enc = self.tok([texts[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False)
            torch.manual_seed(seed * 100003 + bi)
            g = self.model.generate(**enc, max_new_tokens=max_new, do_sample=temperature > 0, temperature=temperature if temperature > 0 else None,
                                    top_p=top_p if temperature > 0 else None, top_k=None, pad_token_id=self.tok.pad_token_id)
            dec = self.tok.batch_decode(g[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            for i, d in zip(idx, dec): outs[i] = d
        return outs
