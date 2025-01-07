import os
import json
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def fetch_questions(text_content, quiz_level):
    # For testing/fallback purposes
    DEFAULT_QUESTIONS = {
        "mcqs": [
            {
                "mcq": "Sample Question 1",
                "options": {
                    "a": "Option A",
                    "b": "Option B",
                    "c": "Option C",
                    "d": "Option D"
                },
                "correct": "a"
            },
            {
                "mcq": "Sample Question 2",
                "options": {
                    "a": "Option A",
                    "b": "Option B",
                    "c": "Option C",
                    "d": "Option D"
                },
                "correct": "b"
            },
            {
                "mcq": "Sample Question 3",
                "options": {
                    "a": "Option A",
                    "b": "Option B",
                    "c": "Option C",
                    "d": "Option D"
                },
                "correct": "c"
            }
        ]
    }

    if not text_content.strip():
        st.warning("Please enter some text content to generate questions.")
        return []

    PROMPT_TEMPLATE = """
    Given the following text, create a quiz with exactly 3 multiple choice questions.
    
    Text: {text_content}
    
    Difficulty level: {quiz_level}
    
    Please format your response as a JSON object with the following structure:
    {{
        "mcqs": [
            {{
                "mcq": "Question text here",
                "options": {{
                    "a": "First option",
                    "b": "Second option",
                    "c": "Third option",
                    "d": "Fourth option"
                }},
                "correct": "a"
            }}
        ]
    }}
    
    Requirements:
    1. Generate exactly 3 questions
    2. Each question must have exactly 4 options (a, b, c, d)
    3. The 'correct' field must contain the letter of the correct answer (a, b, c, or d)
    4. Questions should be relevant to the provided text
    5. Maintain the specified difficulty level: {quiz_level}
    
    Return ONLY the JSON object, no additional text or explanations.
    """

    formatted_prompt = PROMPT_TEMPLATE.format(
        text_content=text_content,
        quiz_level=quiz_level
    )

    try:
        # Add a loading message
        with st.spinner("Generating questions..."):
            completion = client.chat.completions.create(
                model="mixtral-8x7b-32768",  # Updated to use Mixtral model
                messages=[
                    {
                        "role": "user",
                        "content": formatted_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=1,
                stream=False
            )
            
            # Extract the response content
            response_content = completion.choices[0].message.content
            
            # Debug: Display raw response (comment out in production)
            # st.write("Debug - Raw API Response:", response_content)
            
            try:
                # Try to parse the JSON response
                response_data = json.loads(response_content)
                
                # Validate the response structure
                if "mcqs" in response_data and isinstance(response_data["mcqs"], list):
                    return response_data["mcqs"]
                else:
                    st.error("Invalid response structure from API")
                    return DEFAULT_QUESTIONS["mcqs"]
                    
            except json.JSONDecodeError as json_err:
                st.error(f"Failed to parse API response as JSON. Using default questions instead.")
                st.write("Debug - JSON Error:", str(json_err))
                return DEFAULT_QUESTIONS["mcqs"]
                
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return DEFAULT_QUESTIONS["mcqs"]

def main():
    st.title("Quiz Generator App")
    
    # Text Input for user to paste content
    text_content = st.text_area("Paste the text content here:")
    quiz_level = st.selectbox("Select quiz level:", ["Easy", "Medium", "Hard"])
    
    # Initialize session state
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'selected_options' not in st.session_state:
        st.session_state.selected_options = []
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    # Generate Quiz button
    if st.button("Generate Quiz"):
        quiz_level_lower = quiz_level.lower()
        st.session_state.questions = fetch_questions(
            text_content=text_content,
            quiz_level=quiz_level_lower
        )
        st.session_state.selected_options = [None] * len(st.session_state.questions)
        st.session_state.submitted = False

    # Display questions only if they exist
    if st.session_state.questions:
        for i, question in enumerate(st.session_state.questions):
            st.subheader(f"Question {i+1}")
            st.write(question["mcq"])
            options = [(key, value) for key, value in question["options"].items()]
            selected_option = st.radio(
                "Select your answer:",
                options,
                format_func=lambda x: x[1],  # Display the option text, not the key
                key=f"question_{i}",
                index=None
            )
            if selected_option:
                st.session_state.selected_options[i] = selected_option[0]  # Store the key (a, b, c, d)

        # Submit button
        if st.button("Submit Quiz"):
            st.session_state.submitted = True

        # Display final score
            score_percentage = (marks / len(st.session_state.questions)) * 100
            st.subheader("Final Score")
            st.write(f"You got {marks} out of {len(st.session_state.questions)} questions correct ({score_percentage:.1f}%)")
            
        # Show results after submission
        if st.session_state.submitted:
            marks = 0
            st.header("Quiz Results")
            
            for i, question in enumerate(st.session_state.questions):
                selected_key = st.session_state.selected_options[i]
                correct_key = question["correct"]
                
                st.subheader(f"Question {i+1}")
                st.write(question["mcq"])
                st.write(f"Your answer: {question['options'].get(selected_key, 'No answer selected')}")
                st.write(f"Correct answer: {question['options'][correct_key]}")
                
                if selected_key == correct_key:
                    marks += 1
                    st.success("Correct! ✅")
                else:
                    st.error("Incorrect ❌")
                
                st.markdown("---")

if __name__ == "__main__":
    main()
