import requests
import random
import html

EDUCATION_CATEGORY =9
API_URL=f"https://opentdb.com/api.php?amount=10&category={EDUCATION_CATEGORY_ID}&type=multiple"

def get_education_question():
    response = requests.get(API_URL)
    data = response.json()
    question = data["results"][0]
    return question

def run_quiz():
    question = get_education_question()
    print(html.unescape(question["question"]))
    print(f"Options: {question['incorrect_answers']}")
    print("Enter your answer (1-4):")
    user_answer = input()
    correct_answer = question["correct_answer"]
    if user_answer == correct_answer:
        print("Correct!")
    else:
        print(f"Wrong! The correct answer is {correct_answer}")


if __name__=="__main__":
    run_quiz()