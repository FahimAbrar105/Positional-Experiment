"""Static configuration: the free models available for querying, across three
providers (OpenRouter, Groq, and Google direct -- see app/core/llm_client.py
for routing).

Edit this list freely -- it's just data. Run `python -m app.core.refresh_models`
to re-check which of the OpenRouter entries are still free.
"""

MODELS = [
    # -- OpenRouter models are commented out: its shared free pool is prone to
    # persistent 429 rate limits across providers. Uncomment any line below to
    # bring a model back, or leave them off in favor of Groq / direct-provider keys.
    # {"id": "liquid/lfm-2.5-2.6b:free", "label": "LFM2.5 2.6B (Liquid AI)", "provider": "openrouter"},
    # {"id": "google/gemma-4-26b-a4b-it:free", "label": "Gemma 4 26B-A4B MoE (Google)", "provider": "openrouter"},
    # {"id": "google/gemma-4-31b-it:free", "label": "Gemma 4 31B dense (Google)", "provider": "openrouter"},
    # {"id": "nvidia/nemotron-3.5-lightning:free", "label": "Nemotron 3.5 Lightning 3B-A (NVIDIA)", "provider": "openrouter"},
    # {"id": "nvidia/nemotron-3-super-120b-a12b:free", "label": "Nemotron 3 Super 12B-A (NVIDIA)", "provider": "openrouter"},
    # {"id": "nvidia/nemotron-3-ultra-550b-a55b:free", "label": "Nemotron 3 Ultra 55B-A (NVIDIA)", "provider": "openrouter"},
    # {"id": "inclusionai/ling-3.0-flash-sante:free", "label": "Ling 3.0 Flash Sante (InclusionAI)", "provider": "openrouter"},
    # {"id": "inclusionai/ling-3.0-flash-fin:free", "label": "Ling 3.0 Flash Fin (InclusionAI)", "provider": "openrouter"},
    # {"id": "dots-studio/dots-3-note-preview:free", "label": "Dots3 Note Preview 16B-A (Dots Studio)", "provider": "openrouter"},
    # {"id": "cohere/north-mini-code:free", "label": "North Mini Code 3B-A (Cohere)", "provider": "openrouter"},

    # -- Groq free tier (needs GROQ_API_KEY) -- recognizable-brand models;
    # reasoning_effort picked per Groq's docs to keep trials fast (see groq_client.py).
    {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B (OpenAI, via Groq)", "provider": "groq", "reasoning_effort": "low"},
    {"id": "openai/gpt-oss-20b", "label": "GPT-OSS 20B (OpenAI, via Groq)", "provider": "groq", "reasoning_effort": "low"},
    {"id": "qwen/qwen3.6-27b", "label": "Qwen3.6 27B (Alibaba, via Groq)", "provider": "groq", "reasoning_effort": "none"},
    {"id": "qwen/qwen3.8-27b", "label": "Qwen3.8 27B (Alibaba, via Groq)", "provider": "groq", "reasoning_effort": "none"},

    # -- Google direct (needs GEMINI_API_KEY, free at aistudio.google.com/apikey) --
    # Gemma has no paid tier at all on Google's own API -- genuinely, permanently
    # free, and rate-limited per project rather than shared across every
    # OpenRouter free-tier user.
    {"id": "gemma-4-26b-a4b-it", "label": "Gemma 4 26B-A4B MoE (Google, direct)", "provider": "google"},
    # 31b dense commented out: Google's own API returns a consistent 500 for it
    # with a system-role message, and times out (90s+) when merged into one
    # user turn instead -- a server-side issue with this variant, not something
    # fixable client-side. 26B above covers Gemma reliably.
    # {"id": "gemma-4-31b-it", "label": "Gemma 4 31B dense (Google, direct)", "provider": "google"},

    # -- OpenAI direct (needs OPENAI_API_KEY) -- gpt-4.1-nano/gpt-4o-mini both
    # require paid credits, but gpt-5.6-luna is available on a free/promotional
    # allowance that OpenAI doesn't expose a way to confirm via API key. CAVEAT:
    # this model rejects temperature=0 outright, so unlike every other model
    # here it can't be made deterministic -- see openai_client.py.
    {"id": "gpt-5.6-luna", "label": "GPT-5.6 Luna (OpenAI, direct, free tier)", "provider": "openai"},
]

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

RESULTS_DIR = "data/results"
