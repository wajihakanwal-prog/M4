import requests
def get_random_joke():
    response = requests.get("https://official-joke-api.appspot.com/jokes/random")
    data = response.json()
    joke = data["setup"] + " " + data["punchline"]
    return joke
def main():
    print("Welcome to the Random Joke Generator ")

    while True:
        print("Press 'q' to quit")
        user_input = input("Press 'r' to get a random joke: ")
        if user_input == "r":
            joke = get_random_joke()
            print(joke)
        elif user_input == "q":
            break
        else:
            print("Invalid input. Please try again.")
if __name__ == "__main__":
    main()
