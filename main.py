import groq
from dotenv import load_dotenv
import os

def generate_quiz(topic):
    client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"Generate a 5-question multiple-choice quiz on the topic: {topic}. Provide four answer choices for each question and indicate the correct answer."
    
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "system", "content": "You are a helpful assistant that generates quizzes."},
                  {"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

# Example usage
topic = "Machine Learning"
quiz = generate_quiz(topic)
print(quiz)