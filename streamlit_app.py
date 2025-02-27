import streamlit as st
import groq
import json
from dotenv import load_dotenv
import os
import re
import plotly.graph_objects as go
import plotly.express as px
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def validate_secrets():
    required_secrets = ["GROQ_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "PARENT_EMAIL"]
    missing_secrets = [secret for secret in required_secrets if secret not in st.secrets]
    if missing_secrets:
        st.error(f"Missing required secrets: {', '.join(missing_secrets)}")
        st.info("Please add the required secrets to your .streamlit/secrets.toml file")
        return False
    return True

def format_response_to_json(raw_response):
    """Clean and format the API response to ensure valid JSON"""
    try:
        # First try direct JSON parsing
        return json.loads(raw_response)
    except json.JSONDecodeError:
       
        try:
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
        # Use secret instead of hardcoded API key
        client = groq.Client(api_key=st.secrets["GROQ_API_KEY"])
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

def format_time(seconds):
    """Convert seconds to minutes and seconds format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes} minutes and {seconds} seconds"


def send_email_report(topic, difficulty, score, total_time, correct_answers, total_questions, questions_per_minute):
    """Send quiz results via email"""
    try:
        # Email configuration
        sender_email = st.secrets["GMAIL_ADDRESS"]  # Your Gmail address
        sender_password = st.secrets["GMAIL_APP_PASSWORD"]  # Your Gmail app password
        receiver_email = st.secrets["PARENT_EMAIL"]  # Your email to receive reports
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"Quiz Report - {topic} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        
        # Email body
        body = f"""
        Quiz Report Details:
        
        Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        Topic: {topic}
        Difficulty Level: {difficulty}
        
        Performance Summary:
        - Score: {score:.1f}%
        - Correct Answers: {correct_answers} out of {total_questions}
        - Total Time Taken: {format_time(total_time)}
        - Average Speed: {questions_per_minute:.1f} questions per minute
        
        This is an automated report generated by the Quiz Application.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"Failed to send email report: {str(e)}")
        return False

def main():
    st.title("Quiz Generator")
    
    # Validate secrets before proceeding
    if not validate_secrets():
        return
    
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
                st.session_state.start_time = time.time()
                st.session_state.current_topic = topic
                st.session_state.current_difficulty = difficulty
    
    # Display quiz if it exists in session state
    if 'quiz' in st.session_state:
        st.header(f"{st.session_state.current_difficulty.title()} Level Quiz on {st.session_state.current_topic}")
        
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
                st.session_state.total_time = time.time() - st.session_state.start_time
        
        # Show results if quiz is submitted
        if st.session_state.quiz_submitted:
            correct_answers = 0
            incorrect_answers = 0
            st.header("Quiz Results")
            
            # Display total time taken
            total_time = st.session_state.total_time
            total_time_formatted = format_time(total_time)
            st.info(f"Total time taken: {total_time_formatted}")
            
            for i, q in enumerate(st.session_state.quiz["questions"]):
                user_ans = st.session_state.user_answers.get(i, None)
                correct_ans = q["correct_answer"]
                
                st.write(f"Question {i+1}:")
                if user_ans == correct_ans:
                    st.success(f"Correct! Your answer: {user_ans}")
                    correct_answers += 1
                else:
                    st.error(f"Wrong. Your answer: {user_ans}, Correct answer: {correct_ans}")
                    incorrect_answers += 1
                
                if "explanation" in q:
                    with st.expander("See explanation"):
                        st.write(q["explanation"])
            
            # Calculate statistics
            total_questions = len(st.session_state.quiz["questions"])
            score_percentage = (correct_answers / total_questions) * 100
            questions_per_minute = total_questions / (total_time / 60)
            
            # Try to send email report
            try:
                if send_email_report(
                    topic=st.session_state.current_topic,
                    difficulty=st.session_state.current_difficulty,
                    score=score_percentage,
                    total_time=total_time,
                    correct_answers=correct_answers,
                    total_questions=total_questions,
                    questions_per_minute=questions_per_minute
                ):
                    st.success("Quiz report has been sent to parent's email!")
            except Exception as e:
                st.error(f"Failed to send email report: {str(e)}")
            
            # Create visualizations
            st.subheader("Result Visualizations")
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie Chart
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Correct', 'Incorrect'],
                    values=[correct_answers, incorrect_answers],
                    hole=.3,
                    marker_colors=['#00CC96', '#EF553B']
                )])
                fig_pie.update_layout(
                    title="Score Distribution",
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar Chart
                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=['Correct', 'Incorrect'],
                        y=[correct_answers, incorrect_answers],
                        marker_color=['#00CC96', '#EF553B']
                    )
                ])
                fig_bar.update_layout(
                    title="Number of Correct vs Incorrect Answers",
                    yaxis_title="Number of Questions",
                    height=400
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Display final score with difficulty level
            st.header(f"Final Score: {score_percentage:.1f}% ({st.session_state.current_difficulty.title()} Level)")
            
            # Add time-based performance assessment
            st.write(f"Average time per question: {format_time(total_time / total_questions)}")
            st.write(f"Questions answered per minute: {questions_per_minute:.1f}")
            
            # Score interpretation based on difficulty and time
            if score_percentage >= 80:
                msg = {
                    "easy": "Excellent! You're ready for medium difficulty!",
                    "medium": "Outstanding! Try hard difficulty next!",
                    "hard": "Impressive mastery of advanced concepts!"
                }
                st.success(msg[st.session_state.current_difficulty])
            elif score_percentage >= 60:
                st.info("Good job! Keep practicing to improve your score.")
            else:
                st.warning("You might want to review the topic and try again.")
            
            if st.button("Try Another Quiz"):
                # Clean up all session state variables
                for key in ['quiz', 'user_answers', 'quiz_submitted', 'start_time', 
                          'total_time', 'current_topic', 'current_difficulty']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.experimental_rerun()

if __name__ == "__main__":
    load_dotenv()
    main()
