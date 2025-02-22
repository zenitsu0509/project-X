import streamlit as st
import groq
import json
from dotenv import load_dotenv
import os
import re

def format_response_to_json(raw_response):
    """Clean and format the API response to ensure valid JSON"""
    try:
        # First try direct JSON parsing
        return json.loads(raw_response)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON-like content
        try:
            # Look for content between curly braces
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                raise ValueError("No JSON-like content found in response")
        except Exception as e:
            st.error(f"Error formatting response: {str(e)}")
            return None

def get_difficulty_description(difficulty):
    descriptions = {
        "easy": "basic concepts and straightforward questions suitable for beginners",
        "medium": "intermediate concepts with some complexity, requiring good understanding",
        "hard": "advanced concepts with complex scenarios, requiring deep understanding and critical thinking"
    }
    return descriptions.get(difficulty, "")

def generate_quiz(topic, number, difficulty):
    try:
        client = groq.Client(api_key=st.secrets('GROQ_API_KEY'))
        difficulty_desc = get_difficulty_description(difficulty)
        
        prompt = f"""Generate a {number}-question multiple-choice quiz on the topic: {topic}.
        The questions should be at {difficulty.upper()} difficulty level, meaning {difficulty_desc}.
        
        For EASY questions: Focus on basic definitions, simple concepts, and straightforward applications.
        For MEDIUM questions: Include scenario-based problems, relationships between concepts, and moderate complexity.
        For HARD questions: Incorporate complex scenarios, advanced applications, and questions requiring synthesis of multiple concepts.
        
        The response MUST be a valid JSON object in EXACTLY this format:
        {{
            "questions": [
                {{
                    "question": "Question text here",
                    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
                    "correct_answer": "A",
                    "explanation": "Brief explanation of why this answer is correct"
                }}
            ]
        }}"""

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generator that MUST return responses in valid JSON format only."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        raw_content = response.choices[0].message.content
        quiz_data = format_response_to_json(raw_content)
        
        if quiz_data is None:
            st.error("Failed to generate a valid quiz. Please try again.")
            return None
            
        if not isinstance(quiz_data, dict) or "questions" not in quiz_data:
            st.error("Invalid quiz format. Please try again.")
            return None
            
        return quiz_data

    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None

def main():
    st.title("Quiz Generator")
    
    # Input section with difficulty selection
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input("Enter the topic for the quiz:")
        num_questions = st.number_input("Number of questions:", min_value=1, max_value=10, value=5)
    
    with col2:
        difficulty = st.select_slider(
            "Select difficulty level:",
            options=["easy", "medium", "hard"],
            value="medium"
        )
        
        # Show difficulty description
        st.info(f"**{difficulty.title()} Level**: {get_difficulty_description(difficulty)}")
    
    if st.button("Generate Quiz"):
        if not topic:
            st.warning("Please enter a topic")
            return
            
        with st.spinner(f"Generating {difficulty} level quiz..."):
            quiz_data = generate_quiz(topic, num_questions, difficulty)
            if quiz_data:
                st.session_state.quiz = quiz_data
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
    
    # Display quiz if it exists in session state
    if 'quiz' in st.session_state:
        st.header(f"{difficulty.title()} Level Quiz on {topic}")
        
        for i, q in enumerate(st.session_state.quiz["questions"]):
            st.subheader(f"Question {i+1}")
            st.write(q["question"])
            
            # Radio buttons for options
            answer = st.radio(
                "Select your answer:",
                q["options"],
                key=f"q_{i}",
                index=None
            )
            
            # Store user's answer
            if answer:
                st.session_state.user_answers[i] = answer[0]
            
            st.markdown("---")
        
        # Submit button
        if st.button("Submit Quiz"):
            if len(st.session_state.user_answers) < len(st.session_state.quiz["questions"]):
                st.warning("Please answer all questions before submitting.")
            else:
                st.session_state.quiz_submitted = True
            
        # Show results if quiz is submitted
        if st.session_state.quiz_submitted:
            correct_answers = 0
            st.header("Quiz Results")
            
            for i, q in enumerate(st.session_state.quiz["questions"]):
                user_ans = st.session_state.user_answers.get(i, None)
                correct_ans = q["correct_answer"]
                
                st.write(f"Question {i+1}:")
                if user_ans == correct_ans:
                    st.success(f"Correct! Your answer: {user_ans}")
                    correct_answers += 1
                else:
                    st.error(f"Wrong. Your answer: {user_ans}, Correct answer: {correct_ans}")
                
                # Display explanation
                if "explanation" in q:
                    with st.expander("See explanation"):
                        st.write(q["explanation"])
            
            # Display final score with difficulty level
            score_percentage = (correct_answers / len(st.session_state.quiz["questions"])) * 100
            st.header(f"Final Score: {score_percentage:.1f}% ({difficulty.title()} Level)")
            
            # Score interpretation based on difficulty
            if score_percentage >= 80:
                msg = {
                    "easy": "Excellent! You're ready for medium difficulty!",
                    "medium": "Outstanding! Try hard difficulty next!",
                    "hard": "Impressive mastery of advanced concepts!"
                }
                st.success(msg[difficulty])
            elif score_percentage >= 60:
                st.info("Good job! Keep practicing to improve your score.")
            else:
                st.warning("You might want to review the topic and try again.")
            
            if st.button("Try Another Quiz"):
                del st.session_state.quiz
                del st.session_state.user_answers
                del st.session_state.quiz_submitted
                st.experimental_rerun()

if __name__ == "__main__":
    load_dotenv()
    main()
