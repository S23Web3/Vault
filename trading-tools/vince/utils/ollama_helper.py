#!/usr/bin/env python3
"""
Ollama Helper - Wrapper for calling Ollama API programmatically

Usage:
    from vince.utils.ollama_helper import generate_code

    code = generate_code(
        prompt="Write a Python function to calculate Sharpe ratio",
        model="qwen3-coder:30b"
    )
    print(code)
"""

import requests
import json
from typing import Optional

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def generate_code(prompt: str, model: str = "qwen3-coder:30b", stream: bool = False) -> str:
    """
    Generate code using Ollama API.

    Args:
        prompt: The code generation prompt
        model: Ollama model to use (default: qwen3-coder:30b)
        stream: Whether to stream the response (default: False)

    Returns:
        Generated code as string

    Example:
        >>> code = generate_code("Write a function to calculate ATR")
        >>> print(code)
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()

        if stream:
            # Handle streaming response
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if not chunk.get('done'):
                        yield chunk['response']
        else:
            # Handle single response
            result = response.json()
            return result['response']

    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Could not connect to Ollama API. "
            "Make sure Ollama is running: 'ollama serve'"
        )
    except Exception as e:
        raise RuntimeError(f"Ollama API error: {e}")


def generate_with_context(prompt: str, context: str, model: str = "qwen3-coder:30b") -> str:
    """
    Generate code with additional context.

    Args:
        prompt: The main prompt
        context: Additional context (e.g., existing code, documentation)
        model: Ollama model to use

    Returns:
        Generated code
    """
    full_prompt = f"{context}\n\n{prompt}"
    return generate_code(full_prompt, model)


def chat(messages: list[dict], model: str = "qwen3-coder:30b") -> str:
    """
    Chat with Ollama (conversation mode).

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Ollama model to use

    Returns:
        Assistant's response

    Example:
        >>> messages = [
        ...     {"role": "user", "content": "Write a function to calculate RSI"},
        ...     {"role": "assistant", "content": "[previous code]"},
        ...     {"role": "user", "content": "Now add error handling"}
        ... ]
        >>> response = chat(messages)
    """
    # Ollama chat API endpoint
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['message']['content']

    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Could not connect to Ollama API. "
            "Make sure Ollama is running: 'ollama serve'"
        )
    except Exception as e:
        raise RuntimeError(f"Ollama chat API error: {e}")


# Example usage
if __name__ == "__main__":
    # Test 1: Simple code generation
    print("Test 1: Generate Sharpe ratio function")
    code = generate_code(
        prompt="Write a Python function to calculate Sharpe ratio from a pandas Series of returns. Include type hints and docstring."
    )
    print(code)
    print("\n" + "="*60 + "\n")

    # Test 2: Code generation with context
    print("Test 2: Generate with context")
    context = """
    You are working on a trading backtester. Here's the Position class:

    class Position:
        def __init__(self, entry_price, size, direction):
            self.entry_price = entry_price
            self.size = size
            self.direction = direction  # 'LONG' or 'SHORT'
    """

    code = generate_with_context(
        prompt="Add a method to calculate unrealized P&L given current price",
        context=context
    )
    print(code)
    print("\n" + "="*60 + "\n")

    # Test 3: Chat mode
    print("Test 3: Chat conversation")
    messages = [
        {"role": "user", "content": "Write a function to calculate moving average"},
        {"role": "assistant", "content": "def moving_average(data, window): return data.rolling(window).mean()"},
        {"role": "user", "content": "Now add exponential moving average"}
    ]

    response = chat(messages)
    print(response)
