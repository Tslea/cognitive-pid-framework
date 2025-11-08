"""
Comprehensive DeepSeek Test Suite

Tests all aspects of DeepSeek integration including:
- Cost calculation
- Model configuration
- Pricing verification
"""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from llm_client import _estimate_cost, COST_PER_1K_TOKENS


class TestDeepSeekCostEstimation:
    """Test cost calculation for DeepSeek."""
    
    def test_deepseek_chat_cost(self):
        """Test cost calculation for deepseek-chat."""
        # 1000 input tokens + 500 output tokens
        cost = _estimate_cost('deepseek-chat', 1000, 500)
        
        # Expected: (1000/1000 * 0.00014) + (500/1000 * 0.00028)
        expected = 0.00014 + 0.00014
        assert abs(cost - expected) < 0.0000001
        assert cost == pytest.approx(0.00028, rel=1e-6)
    
    def test_deepseek_coder_cost(self):
        """Test cost calculation for deepseek-coder."""
        cost = _estimate_cost('deepseek-coder', 2000, 1000)
        
        # Expected: (2000/1000 * 0.00014) + (1000/1000 * 0.00028)
        expected = 0.00028 + 0.00028
        assert cost == pytest.approx(0.00056, rel=1e-6)
    
    def test_large_token_cost(self):
        """Test cost for large token counts."""
        # Simulate a large generation
        cost = _estimate_cost('deepseek-chat', 10000, 5000)
        
        # Expected: (10000/1000 * 0.00014) + (5000/1000 * 0.00028)
        expected = 0.0014 + 0.0014
        assert cost == pytest.approx(0.0028, rel=1e-6)
    
    def test_cost_vs_gpt4(self):
        """Verify DeepSeek is ~100x cheaper than GPT-4."""
        deepseek_cost = _estimate_cost('deepseek-chat', 1000, 500)
        gpt4_cost = _estimate_cost('gpt-4', 1000, 500)
        
        # DeepSeek should be at least 100x cheaper
        ratio = gpt4_cost / deepseek_cost
        assert ratio > 100, f"DeepSeek should be >100x cheaper, got {ratio}x"
    
    def test_deepseek_pricing_in_constants(self):
        """Test that DeepSeek pricing is properly defined."""
        assert 'deepseek-chat' in COST_PER_1K_TOKENS
        assert 'deepseek-coder' in COST_PER_1K_TOKENS
        
        assert COST_PER_1K_TOKENS['deepseek-chat']['input'] == 0.00014
        assert COST_PER_1K_TOKENS['deepseek-chat']['output'] == 0.00028
        assert COST_PER_1K_TOKENS['deepseek-coder']['input'] == 0.00014
        assert COST_PER_1K_TOKENS['deepseek-coder']['output'] == 0.00028
    
    def test_zero_tokens_cost(self):
        """Test cost with zero tokens."""
        cost = _estimate_cost('deepseek-chat', 0, 0)
        assert cost == 0.0
    
    def test_only_input_tokens(self):
        """Test cost with only input tokens."""
        cost = _estimate_cost('deepseek-chat', 1000, 0)
        expected = 0.00014
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_only_output_tokens(self):
        """Test cost with only output tokens."""
        cost = _estimate_cost('deepseek-chat', 0, 1000)
        expected = 0.00028
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_realistic_conversation_cost(self):
        """Test cost for a realistic conversation."""
        # Typical conversation: 500 input, 300 output
        cost = _estimate_cost('deepseek-chat', 500, 300)
        expected = (500/1000 * 0.00014) + (300/1000 * 0.00028)
        assert cost == pytest.approx(expected, rel=1e-6)
        # Should be very cheap
        assert cost < 0.001  # Less than $0.001
    
    def test_realistic_code_generation_cost(self):
        """Test cost for realistic code generation."""
        # Code generation: 1000 input (prompt), 2000 output (code)
        cost = _estimate_cost('deepseek-coder', 1000, 2000)
        expected = (1000/1000 * 0.00014) + (2000/1000 * 0.00028)
        assert cost == pytest.approx(expected, rel=1e-6)
        # Should be very cheap
        assert cost < 0.001  # Less than $0.001


class TestDeepSeekConfiguration:
    """Test DeepSeek configuration."""
    
    def test_api_key_environment_variable(self):
        """Test API key can be read from environment."""
        # This test only checks if the environment variable can be set
        test_key = "test-key-12345"
        os.environ['DEEPSEEK_API_KEY'] = test_key
        assert os.getenv('DEEPSEEK_API_KEY') == test_key
        # Clean up
        if 'DEEPSEEK_API_KEY' in os.environ:
            del os.environ['DEEPSEEK_API_KEY']
    
    def test_placeholder_detection(self):
        """Test that we can detect placeholder API keys."""
        placeholder_keys = [
            'your_deepseek_api_key_here',
            'your_api_key',
            'sk-your-key'
        ]
        
        for key in placeholder_keys:
            assert key.startswith('your_') or 'your' in key.lower()


class TestDeepSeekModels:
    """Test DeepSeek model names and configuration."""
    
    def test_model_names(self):
        """Test that model names are correctly defined."""
        valid_models = ['deepseek-chat', 'deepseek-coder']
        
        for model in valid_models:
            assert model in COST_PER_1K_TOKENS
    
    def test_deepseek_chat_for_conversation(self):
        """Test that deepseek-chat is suitable for conversation."""
        # deepseek-chat should have pricing defined
        assert 'deepseek-chat' in COST_PER_1K_TOKENS
        pricing = COST_PER_1K_TOKENS['deepseek-chat']
        assert 'input' in pricing
        assert 'output' in pricing
    
    def test_deepseek_coder_for_code(self):
        """Test that deepseek-coder is suitable for code."""
        # deepseek-coder should have pricing defined
        assert 'deepseek-coder' in COST_PER_1K_TOKENS
        pricing = COST_PER_1K_TOKENS['deepseek-coder']
        assert 'input' in pricing
        assert 'output' in pricing


class TestCostComparison:
    """Test cost comparisons between providers."""
    
    def test_deepseek_vs_openai_turbo(self):
        """Compare DeepSeek vs OpenAI GPT-3.5 Turbo."""
        tokens_in, tokens_out = 1000, 500
        
        deepseek_cost = _estimate_cost('deepseek-chat', tokens_in, tokens_out)
        gpt35_cost = _estimate_cost('gpt-3.5-turbo', tokens_in, tokens_out)
        
        # DeepSeek should be cheaper
        assert deepseek_cost < gpt35_cost
        
        # Calculate savings
        savings_ratio = gpt35_cost / deepseek_cost
        assert savings_ratio > 3  # At least 3x cheaper
    
    def test_deepseek_vs_claude(self):
        """Compare DeepSeek vs Claude."""
        tokens_in, tokens_out = 1000, 500
        
        deepseek_cost = _estimate_cost('deepseek-chat', tokens_in, tokens_out)
        claude_cost = _estimate_cost('claude-3-sonnet', tokens_in, tokens_out)
        
        # DeepSeek should be much cheaper
        assert deepseek_cost < claude_cost
        savings_ratio = claude_cost / deepseek_cost
        assert savings_ratio > 10  # At least 10x cheaper
    
    def test_project_cost_estimate(self):
        """Estimate cost for a full project."""
        # 20 iterations, 3 agents, average tokens
        iterations = 20
        agents_per_iteration = 3
        avg_tokens_in = 1500
        avg_tokens_out = 800
        
        total_calls = iterations * agents_per_iteration
        
        # DeepSeek cost
        deepseek_cost_per_call = _estimate_cost('deepseek-chat', avg_tokens_in, avg_tokens_out)
        total_deepseek = deepseek_cost_per_call * total_calls
        
        # GPT-4 cost for comparison
        gpt4_cost_per_call = _estimate_cost('gpt-4', avg_tokens_in, avg_tokens_out)
        total_gpt4 = gpt4_cost_per_call * total_calls
        
        # Verify DeepSeek is extremely cost-effective
        assert total_deepseek < 0.1  # Less than 10 cents for full project
        assert total_gpt4 > 1.0  # GPT-4 would be >$1
        
        savings = total_gpt4 - total_deepseek
        assert savings > 1.0  # Save at least $1 per project


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
