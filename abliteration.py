import torch
import functools
import einops
import gc

import os
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm
from torch import Tensor
from typing import List
from transformer_lens import TransformerBridge, utilities
from transformer_lens.hook_points import HookPoint
from transformers import AutoModelForCausalLM, AutoTokenizer
from jaxtyping import Float, Int
from collections import defaultdict

# Turn automatic differentiation off to save GPU memory (credit: Undi95)
torch.set_grad_enabled(False)

def reformat_texts(texts):
    return [[{"role": "user", "content": text}] for text in texts]

# Get harmful and harmless datasets
def get_harmful_instructions():
    dataset = load_dataset('mlabonne/harmful_behaviors')
    return reformat_texts(dataset['train']['text']), reformat_texts(dataset['test']['text'])

def get_harmless_instructions():
    dataset = load_dataset('mlabonne/harmless_alpaca')
    return reformat_texts(dataset['train']['text']), reformat_texts(dataset['test']['text'])

harmful_inst_train, harmful_inst_test = get_harmful_instructions()
harmless_inst_train, harmless_inst_test = get_harmless_instructions()

# Option A: Path relative to this exact script (abliteration.py)
script_dir = Path(__file__).parent.resolve()
local_model_path = str(script_dir / "my_local_qwen_model")

if not os.path.isdir(local_model_path):
    raise FileNotFoundError(f"Directory not found: {local_model_path}")

# Check for essential files
required_files = ["config.json", "tokenizer_config.json"]
missing = [f for f in required_files if not os.path.exists(os.path.join(local_model_path, f))]
if missing:
    raise FileNotFoundError(f"Missing expected files in {local_model_path}: {missing}")


# Resolve absolute path
local_model_path = str((Path(__file__).parent / "my_local_qwen_model").resolve())

# 1. Load Tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    local_model_path,
    local_files_only=True
)
tokenizer.padding_side = 'left'
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 2. Boot Model in TransformerLens 4.x
model = TransformerBridge.boot_transformers(
    local_model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# 3. Enable numeric equivalence
model.enable_compatibility_mode()