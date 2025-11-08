"""Test rapido DeepSeek."""
import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
from llm_client import call_llm

load_dotenv()

print("🧪 Testing DeepSeek connection...")
print("=" * 60)

try:
    response = call_llm(
        prompt="Rispondi in italiano: Ciao! Il sistema funziona?",
        model="deepseek-chat",
        provider="deepseek",
        temperature=0.7,
        max_tokens=100
    )
    
    print("✅ DeepSeek Response:")
    print(response)
    print("=" * 60)
    print("✅ Sistema pronto! Puoi usare il framework.")
    
except Exception as e:
    print(f"❌ Errore: {e}")
    print("\nVerifica che DEEPSEEK_API_KEY sia configurato in .env")
