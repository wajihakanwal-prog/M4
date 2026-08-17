#pip install requests
# config.py

HF_API_KEY = "123"
import requests

from config import HF_API_KEY

MODEl_ID="facebook/bart-large-mnli"
API_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}
TOPICS=["Sports","Technology","Business","Politics","Health"]

def ask_hf(headline):
    payload = {"inputs": headline,"parameters":{"candidates_label":TOPICS}}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if not response.ok:
        raise Exception(f"Request failed with status {response.status_code} and response {response.text}")  
    return response.json()["generated_text"]

def best_topics(preds:list):
    best=max(preds,key=lambda x:x["score"])
    return best["label"],best["score"]
def bar(score:float)->str:
    pct=score*100
    blocks=int(pct//10)
    return "█"*blocks+"░"*(10-blocks)
def show(headline:str, preds:list):
    top_label   ,top_score=best_topics(preds)
    print(f"Headline: {headline}")
    print(f"Top topic: {top_label} ({bar(top_score)})")
    print(f"Other topics:")
    for label,score in preds:
        if label==top_label:continue
        print(f"{label} ({bar(score)})")
    top3=sorted(preds,key=lambda x:x["score"],reverse=True)[:3]
    print(f"Top 3 topics: {top3}")
    for i , p in enumerate(top3, start=1):
            print(f"{i}. {p['label']:<11} {round(p['score']*100,1)}% [{bar(p['score'])}]")

    print("=" * 60)

def main():
     
     print("Enter the headline you want to analyze:")
     while True:
          headline=input("Headline: ").strip()
          if headline.lower()=="exit":  
               print("Exiting...")
               break
          if not headline:
               print("Please enter a headline.")
               continue
          try:
               preds=ask_hf(headline)
               if isinstance(preds,dict):
                    show(headline,preds["preds"])
               else:
                    show(headline,preds)
          except Exception as e:
               print(f"An error occurred: {e}")
               print("Please try again.")

if __name__ == "__main__":
    main()
        
    
               