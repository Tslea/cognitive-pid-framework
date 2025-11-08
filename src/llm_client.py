"""
LLM Client

Unified client for calling different LLM providers (OpenAI, Anthropic, etc.)
with retry logic and cost tracking.
"""

import logging
import os
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential


# Cost tracking (tokens × price per 1K tokens)
COST_PER_1K_TOKENS = {
    'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
    'gpt-4': {'input': 0.03, 'output': 0.06},
    'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
    'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
    'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
    # DeepSeek - extremely cost-effective!
    'deepseek-chat': {'input': 0.00014, 'output': 0.00028},  # $0.14/$0.28 per 1M tokens
    'deepseek-coder': {'input': 0.00014, 'output': 0.00028},
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def call_llm(
    prompt: str,
    model: str = 'gpt-3.5-turbo',
    temperature: float = 0.7,
    max_tokens: int = 2000,
    provider: str = 'openai'
) -> str:
    """Call LLM API with retry logic.
    
    Args:
        prompt: Input prompt
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        provider: 'openai' or 'anthropic'
        
    Returns:
        Generated text response
        
    Raises:
        Exception: If API call fails after retries
    """
    logger = logging.getLogger(__name__)
    
    if provider == 'openai':
        return _call_openai(prompt, model, temperature, max_tokens)
    elif provider == 'anthropic':
        return _call_anthropic(prompt, model, temperature, max_tokens)
    elif provider == 'deepseek':
        return _call_deepseek(prompt, model, temperature, max_tokens)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _call_openai(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    """Call OpenAI API.
    
    Args:
        prompt: Input prompt
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        
    Returns:
        Generated text
    """
    logger = logging.getLogger(__name__)
    
    try:
        import openai
        
        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Create client
        client = openai.OpenAI(api_key=api_key)
        
        # Call API
        logger.debug(f"Calling OpenAI {model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract response
        text = response.choices[0].message.content
        
        # Track cost (approximate)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = _estimate_cost(model, input_tokens, output_tokens)
        
        logger.info(
            f"OpenAI {model}: {input_tokens} in, {output_tokens} out, "
            f"${cost:.4f}"
        )
        
        return text
        
    except ImportError:
        logger.error("OpenAI package not installed. Run: pip install openai")
        raise
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise


def _call_anthropic(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    """Call Anthropic API.
    
    Args:
        prompt: Input prompt
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        
    Returns:
        Generated text
    """
    logger = logging.getLogger(__name__)
    
    try:
        import anthropic
        
        # Get API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        # Create client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Call API
        logger.debug(f"Calling Anthropic {model}")
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract response
        text = message.content[0].text
        
        # Track cost (approximate)
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = _estimate_cost(model, input_tokens, output_tokens)
        
        logger.info(
            f"Anthropic {model}: {input_tokens} in, {output_tokens} out, "
            f"${cost:.4f}"
        )
        
        return text
        
    except ImportError:
        logger.error("Anthropic package not installed. Run: pip install anthropic")
        raise
    except Exception as e:
        logger.error(f"Anthropic API call failed: {e}")
        raise


def _call_deepseek(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    """Call DeepSeek API (OpenAI-compatible).
    
    Args:
        prompt: Input prompt
        model: Model name (e.g., 'deepseek-chat' or 'deepseek-coder')
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        
    Returns:
        Generated text
    """
    logger = logging.getLogger(__name__)
    
    try:
        import openai
        
        # Get API key from environment
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")
        
        # Create client with DeepSeek base URL
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # Call API (OpenAI-compatible interface)
        logger.debug(f"Calling DeepSeek {model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract response
        text = response.choices[0].message.content
        
        # Track cost (approximate)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = _estimate_cost(model, input_tokens, output_tokens)
        
        logger.info(
            f"DeepSeek {model}: {input_tokens} in, {output_tokens} out, "
            f"${cost:.4f} (extremely cost-effective!)"
        )
        
        return text
        
    except ImportError:
        logger.error("OpenAI package not installed. Run: pip install openai")
        raise
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {e}")
        raise


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate API call cost.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    # Find matching model pricing
    pricing = None
    for model_prefix, model_pricing in COST_PER_1K_TOKENS.items():
        if model.startswith(model_prefix):
            pricing = model_pricing
            break
    
    if not pricing:
        # Default to gpt-3.5-turbo pricing
        pricing = COST_PER_1K_TOKENS['gpt-3.5-turbo']
    
    input_cost = (input_tokens / 1000) * pricing['input']
    output_cost = (output_tokens / 1000) * pricing['output']
    
    return input_cost + output_cost
