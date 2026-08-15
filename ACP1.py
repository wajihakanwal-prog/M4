import requests
import json
from datetime import datetime

class GitHubAPI:
    def __init__(self):
        self.base_url = "https://api.github.com"
    
    def get_user_info(self, username):
        """Fetch GitHub user information"""
        try:
            response = requests.get(f"{self.base_url}/users/{username}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user info: {e}")
            return None
    
    def get_user_repos(self, username, limit=5):
        """Fetch user repositories"""
        try:
            params = {'sort': 'updated', 'per_page': limit}
            response = requests.get(f"{self.base_url}/users/{username}/repos", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repos: {e}")
            return None
    
    def get_user_events(self, username, limit=5):
        """Fetch user recent events"""
        try:
            params = {'per_page': limit}
            response = requests.get(f"{self.base_url}/users/{username}/events", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching events: {e}")
            return None
    
    def display_user_info(self, user_info):
        """Display GitHub user information"""
        if not user_info:
            return
        
        print("\n" + "="*50)
        print(f"👤 GitHub User: {user_info['login']}")
        print("="*50)
        print(f"Name: {user_info.get('name', 'N/A')}")
        print(f"Bio: {user_info.get('bio', 'No bio provided')}")
        print(f"Location: {user_info.get('location', 'N/A')}")
        print(f"Public Repos: {user_info.get('public_repos', 0)}")
        print(f"Followers: {user_info.get('followers', 0)}")
        print(f"Following: {user_info.get('following', 0)}")
        print(f"Profile: {user_info.get('html_url', 'N/A')}")
        print("="*50)
    
    def display_repos(self, repos):
        """Display repository information"""
        if not repos:
            print("No repositories found")
            return
        
        print("\n📚 Recent Repositories:")
        print("-"*50)
        for repo in repos:
            print(f"📁 {repo['name']}")
            print(f"   Description: {repo.get('description', 'No description')}")
            print(f"   ⭐ Stars: {repo.get('stargazers_count', 0)}")
            print(f"   🍴 Forks: {repo.get('forks_count', 0)}")
            print(f"   Language: {repo.get('language', 'N/A')}")
            print(f"   URL: {repo['html_url']}")
            print()

# Test the GitHub API
github_api = GitHubAPI()
username = "octocat"  # Example user
user_info = github_api.get_user_info(username)
if user_info:
    github_api.display_user_info(user_info)
    repos = github_api.get_user_repos(username)
    github_api.display_repos(repos)