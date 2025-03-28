import ollama
import json


def analyze_with_llm(baseline_avg, stress_avg, error_rate):
    """Use local LLM to interpret experiment results"""
    prompt = f"""
    Analyze these web service performance metrics:
    - Baseline latency: {baseline_avg:.3f} seconds
    - Stressed latency: {stress_avg:.3f} seconds
    - Error rate during stress: {error_rate:.1%}

    Provide:
    1. Performance degradation analysis
    2. Three potential system bottlenecks
    3. Recommended optimizations

    Return JSON with: analysis, bottlenecks, recommendations
    """

    response = ollama.generate(
        model='gemma3:latest',
        prompt=prompt,
        format='json'
    )

    try:
        return json.loads(response['response'])
    except:
        return {"error": "Analysis failed"}


# Example usage:
results = analyze_with_llm(0.25, 1.78, 0.15)
print(json.dumps(results, indent=2))