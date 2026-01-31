import openrouter
openrouter.api_key = "YOUR_OPENROUTER_API_KEY"

try:
    response = openrouter.requests.models.generate(
        model="google/gemma-27b-it",
        prompt="Write a short sentence about cats.",
        max_tokens=100,
        temperature=0.7
    )

    print(response)

except Exception as e:
    print(f"Error: {e}")
