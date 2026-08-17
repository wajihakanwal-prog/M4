import requests
from config import API_KEY, API_URL

def summarize_text(text):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    data = {
        'text': text
    }
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['summary']
    else:
        return None

DEFAULT_MODEL="google/pegasus-xsum"
def build_api_url(model=DEFAULT_MODEL):
    return f"https://api-inference.huggingface.co/models/{model}"

def query(payload ,model_name=DEFAULT_MODEL):
    api_url = build_api_url(model_name)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(api_url, headers=headers, json=payload)
    return response.json()

if __name__ == "__main__":
    print("what is your name")
    user_name=input("Your name :").strip()
    if not user_name:
        print("please enter your name")
        exit(1)
    print("Hello",user_name)
    print("What is your text?")
    user_text=input("Your text :").strip()
    if not user_text:
        print("please enter your text")
        exit(1)
    print("Enter the model name")
    model_name=input("Model name :").strip()
    if not model_name:
        print("please enter the model name")
        exit(1)
    print("choose your summerization style ")
    print("1. extractive")
    print("2. abstractive")
    print("3. hybrid")
    choice=int(input("Your choice :"))
    if choice==1:
        print("extractive")
        min_lengt=80
        max_length=200
    elif choice==2:
        print("abstractive")
        min_lengt=50
        max_length=150
    elif choice==3:
        print("hybrid")
    summary=summarize_text(user_text,min_lengt,max_length)

    if summary:
        print(summary)
    else:
        print("Error")
        
