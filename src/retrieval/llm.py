from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from core.config import Settings, normalized_provider, require_llm_credentials


def build_llm(settings: Settings, temperature: float = 0.0):
    provider = normalized_provider(settings)
    require_llm_credentials(settings)

    if provider == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=settings.model_name,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )
        
        # Thêm cơ chế Fallback (tự động chuyển API khi bị giới hạn)
        fallbacks = []
        if settings.openrouter_api_key:
            fallbacks.append(
                ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=settings.openrouter_api_key,
                    base_url=settings.openrouter_base_url or "https://openrouter.ai/api/v1",
                    temperature=temperature,
                )
            )
            
        if settings.custom_llm_base_url:
            base_url = settings.custom_llm_base_url
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"
                
            fallbacks.append(
                ChatOpenAI(
                    model="google/gemma-4-e4b",
                    api_key=settings.custom_llm_api_key or "lm-studio",
                    base_url=base_url,
                    temperature=temperature,
                )
            )
            
        if fallbacks:
            llm = llm.with_fallbacks(fallbacks)
            
        return llm
    if provider == "openai":
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )
    if provider == "anthropic":
        return ChatAnthropic(
            model=settings.model_name,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )
    if provider == "openrouter":
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=temperature,
        )
    if provider == "ollama":
        return ChatOllama(
            model=settings.model_name,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )
    if provider == "custom":
        base_url = settings.custom_llm_base_url
        if base_url and not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
            
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.custom_llm_api_key or "unused",
            base_url=base_url,
            temperature=temperature,
        )
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
