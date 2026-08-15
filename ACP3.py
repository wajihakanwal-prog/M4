import requests
import json
import random
from datetime import datetime
from typing import Dict, List, Optional

class UselessFactsAPI:
    """Handler for the Random Useless Facts API"""
    
    def __init__(self):
        self.base_url = "https://uselessfacts.jsph.pl/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UselessFactsApp/1.0',
            'Accept': 'application/json'
        })
        self.fact_history = []
        self.category_counts = {}
        
    def get_random_fact(self, language: str = 'en') -> Optional[Dict]:
        """
        Fetch a random useless fact
        
        Args:
            language: 'en' for English, 'de' for German, 'es' for Spanish, etc.
        
        Returns:
            Dictionary containing the fact data
        """
        try:
            params = {'language': language}
            response = self.session.get(
                f"{self.base_url}/random",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Log the fact
            self._log_fact(data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching random fact: {e}")
            return None
    
    def get_todays_fact(self, language: str = 'en') -> Optional[Dict]:
        """
        Get today's useless fact (same for everyone today)
        
        Args:
            language: Language code
        
        Returns:
            Dictionary containing today's fact
        """
        try:
            params = {'language': language}
            response = self.session.get(
                f"{self.base_url}/today",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Log the fact
            self._log_fact(data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching today's fact: {e}")
            return None
    
    def get_random_fact_by_category(self, category: str = None) -> Optional[Dict]:
        """
        Get a random fact, optionally by category
        Note: The free API doesn't support categories directly,
        so we'll simulate by fetching multiple and filtering
        """
        try:
            # Fetch multiple facts to filter by category
            facts = []
            for _ in range(5):
                fact = self.get_random_fact()
                if fact:
                    facts.append(fact)
            
            if not facts:
                return None
            
            # If category is specified, try to find a matching fact
            if category:
                for fact in facts:
                    if category.lower() in fact.get('text', '').lower():
                        return fact
            
            # Return a random fact if no category match found
            return random.choice(facts)
            
        except Exception as e:
            print(f"❌ Error fetching category fact: {e}")
            return None
    
    def get_multiple_facts(self, count: int = 5, language: str = 'en') -> List[Dict]:
        """
        Fetch multiple random facts
        
        Args:
            count: Number of facts to fetch (1-10)
            language: Language code
        
        Returns:
            List of fact dictionaries
        """
        facts = []
        for i in range(min(count, 10)):
            fact = self.get_random_fact(language)
            if fact:
                facts.append(fact)
            # Small delay to avoid rate limiting
            if i < count - 1:
                import time
                time.sleep(0.1)
        return facts
    
    def _log_fact(self, fact: Dict):
        """Log fetched facts for history tracking"""
        if fact and 'text' in fact:
            self.fact_history.append({
                'timestamp': datetime.now().isoformat(),
                'fact': fact['text'],
                'source': fact.get('source', 'Unknown'),
                'id': fact.get('id', 'N/A')
            })
            
            # Update category counts (approximate)
            text = fact['text'].lower()
            categories = ['animal', 'food', 'history', 'science', 'sport', 
                         'music', 'art', 'nature', 'human', 'space']
            for category in categories:
                if category in text:
                    self.category_counts[category] = self.category_counts.get(category, 0) + 1
    
    def get_statistics(self) -> Dict:
        """Get usage statistics"""
        return {
            'total_facts_fetched': len(self.fact_history),
            'categories': self.category_counts,
            'last_fetch': self.fact_history[-1]['timestamp'] if self.fact_history else None,
            'unique_facts': len(set([f['fact'] for f in self.fact_history]))
        }
    
    def format_fact(self, fact_data: Dict, show_source: bool = True) -> str:
        """Format a fact for display"""
        if not fact_data:
            return "No fact available"
        
        text = fact_data.get('text', 'Fact not found')
        source = fact_data.get('source', 'Unknown')
        fact_id = fact_data.get('id', 'N/A')
        
        formatted = f"💡 {text}"
        if show_source:
            formatted += f"\n   📚 Source: {source}"
            formatted += f"\n   🆔 ID: {fact_id}"
        
        return formatted

### 3. Interactive Fact Display Application


class FactDisplayApp:
    """Interactive application for displaying useless facts"""
    
    def __init__(self):
        self.api = UselessFactsAPI()
        self.favorite_facts = []
        self.current_fact = None
        
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "="*70)
        print("🤡 RANDOM USELESS FACTS MASTER")
        print("="*70)
        print("Discover fascinatingly useless facts!")
        print("="*70)
    
    def display_main_menu(self):
        """Display the main menu"""
        print("\n📋 MAIN MENU")
        print("-"*50)
        print("1. 🤔 Get Random Fact")
        print("2. 📅 Get Today's Fact")
        print("3. 📚 Get Multiple Facts")
        print("4. 🔍 Search Facts by Category")
        print("5. ⭐ View Favorites")
        print("6. 📊 View Statistics")
        print("7. 🎨 Random Fact Generator (Continuous)")
        print("8. 💾 Export Facts to File")
        print("9. 🧠 Fact of the Day Quiz")
        print("10. ❌ Exit")
        print("-"*50)
    
    def get_random_fact(self):
        """Fetch and display a random fact"""
        print("\n🔄 Fetching random fact...")
        fact = self.api.get_random_fact()
        
        if fact:
            self.current_fact = fact
            print("\n" + "="*50)
            print(self.api.format_fact(fact, show_source=True))
            print("="*50)
            
            # Ask if user wants to save as favorite
            self._ask_favorite()
        else:
            print("❌ Could not fetch a fact. Please try again.")
    
    def get_todays_fact(self):
        """Fetch and display today's fact"""
        print("\n🔄 Fetching today's fact...")
        fact = self.api.get_todays_fact()
        
        if fact:
            self.current_fact = fact
            print("\n" + "="*50)
            print(f"📅 Today's Fact ({datetime.now().strftime('%B %d, %Y')})")
            print("-"*50)
            print(self.api.format_fact(fact, show_source=True))
            print("="*50)
            
            self._ask_favorite()
        else:
            print("❌ Could not fetch today's fact.")
    
    def get_multiple_facts(self):
        """Fetch and display multiple facts"""
        while True:
            try:
                count = int(input("\nHow many facts would you like? (1-10): "))
                if 1 <= count <= 10:
                    break
                else:
                    print("Please enter a number between 1 and 10.")
            except ValueError:
                print("Please enter a valid number.")
        
        print(f"\n🔄 Fetching {count} facts...")
        facts = self.api.get_multiple_facts(count)
        
        if facts:
            print("\n" + "="*60)
            print(f"📚 {count} USELESS FACTS")
            print("="*60)
            
            for i, fact in enumerate(facts, 1):
                print(f"\n{i}. {fact['text']}")
                if 'source' in fact:
                    print(f"   📚 Source: {fact['source']}")
                
            print("\n" + "="*60)
        else:
            print("❌ Could not fetch facts.")
    
    def search_by_category(self):
        """Search for facts by category (simulated)"""
        print("\n🔍 SEARCH BY CATEGORY")
        print("-"*40)
        print("Available categories (simulated):")
        print("  animal, food, history, science, sport")
        print("  music, art, nature, human, space")
        
        category = input("\nEnter category: ").strip().lower()
        
        if not category:
            print("No category entered.")
            return
        
        print(f"\n🔄 Searching for facts about '{category}'...")
        fact = self.api.get_random_fact_by_category(category)
        
        if fact:
            print("\n" + "="*50)
            print(f"📌 Fact about {category.capitalize()}:")
            print("-"*50)
            print(self.api.format_fact(fact, show_source=True))
            print("="*50)
        else:
            print(f"❌ No facts found about '{category}'. Try another category.")
    
    def view_favorites(self):
        """Display favorite facts"""
        if not self.favorite_facts:
            print("\n⭐ You don't have any favorite facts yet.")
            return
        
        print("\n" + "="*60)
        print(f"⭐ YOUR FAVORITE FACTS ({len(self.favorite_facts)})")
        print("="*60)
        
        for i, fact in enumerate(self.favorite_facts, 1):
            print(f"\n{i}. {fact['text']}")
            if 'source' in fact:
                print(f"   📚 Source: {fact['source']}")
            print(f"   📅 Added: {fact.get('added', 'Unknown')}")
        
        print("\n" + "="*60)
    
    def view_statistics(self):
        """Display usage statistics"""
        stats = self.api.get_statistics()
        
        print("\n" + "="*60)
        print("📊 USAGE STATISTICS")
        print("="*60)
        
        print(f"\nTotal Facts Fetched: {stats['total_facts_fetched']}")
        print(f"Unique Facts: {stats['unique_facts']}")
        
        if stats['last_fetch']:
            last_time = datetime.fromisoformat(stats['last_fetch'])
            print(f"Last Fetch: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if stats['categories']:
            print("\n📂 Category Breakdown:")
            sorted_cats = sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_cats[:5]:
                print(f"   {category.capitalize()}: {count}")
        
        print("\n" + "="*60)
    
    def random_fact_generator(self):
        """Continuous random fact generator"""
        print("\n🎨 RANDOM FACT GENERATOR")
        print("-"*40)
        print("Press 'q' to stop, any other key for next fact")
        print("-"*40)
        
        count = 0
        while True:
            fact = self.api.get_random_fact()
            if fact:
                count += 1
                print(f"\n📌 Fact #{count}")
                print(self.api.format_fact(fact, show_source=False))
                
                # Ask for next action
                choice = input("\nPress Enter for next fact, 'q' to quit: ").strip().lower()
                if choice == 'q':
                    break
            else:
                print("❌ Failed to fetch fact. Retrying...")
    
    def export_facts(self):
        """Export fetched facts to a file"""
        if not self.api.fact_history:
            print("\n⚠️ No facts to export. Fetch some facts first.")
            return
        
        filename = f"useless_facts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.api.fact_history, f, indent=2)
            
            print(f"\n✅ Facts exported to '{filename}'")
            print(f"📁 Contains {len(self.api.fact_history)} facts")
        except Exception as e:
            print(f"❌ Error exporting facts: {e}")
    
    def fact_of_the_day_quiz(self):
        """Interactive quiz using facts"""
        print("\n🧠 FACT OF THE DAY QUIZ")
        print("="*50)
        print("Let's test your memory!")
        
        # Get a fact
        fact = self.api.get_random_fact()
        if not fact:
            print("❌ Could not fetch a fact for the quiz.")
            return
        
        fact_text = fact['text']
        print("\n📖 Here's your fact for today:")
        print("-"*40)
        print(fact_text)
        print("-"*40)
        
        # Ask questions about the fact
        score = 0
        questions = [
            ("What is the main subject of this fact?", 1),
            ("Can you recall one key detail from this fact?", 1),
            ("Where does this fact come from?", 2 if fact.get('source') else 1)
        ]
        
        for question, points in questions:
            print(f"\n{question}")
            print(f"(Points: {points})")
            answer = input("Your response: ").strip()
            
            if answer:
                print(f"✅ +{points} points for effort!")
                score += points
            else:
                print("❌ No points this time.")
        
        print("\n" + "="*50)
        print(f"🎉 Quiz Complete! Score: {score}/4")
        
        if score >= 3:
            print("🌟 Great job! You're paying attention!")
        elif score >= 1:
            print("👍 Not bad! Keep practicing!")
        else:
            print("💪 Try again with more focus!")
    
    def _ask_favorite(self):
        """Ask if user wants to save current fact as favorite"""
        if self.current_fact:
            choice = input("\n⭐ Add to favorites? (y/n): ").strip().lower()
            if choice == 'y':
                self.favorite_facts.append({
                    'text': self.current_fact['text'],
                    'source': self.current_fact.get('source', 'Unknown'),
                    'added': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
                print("✅ Added to favorites!")
    
    def run(self):
        """Main application loop"""
        self.display_welcome()
        
        while True:
            self.display_main_menu()
            choice = input("\nSelect option (1-10): ").strip()
            
            if choice == '1':
                self.get_random_fact()
            elif choice == '2':
                self.get_todays_fact()
            elif choice == '3':
                self.get_multiple_facts()
            elif choice == '4':
                self.search_by_category()
            elif choice == '5':
                self.view_favorites()
            elif choice == '6':
                self.view_statistics()
            elif choice == '7':
                self.random_fact_generator()
            elif choice == '8':
                self.export_facts()
            elif choice == '9':
                self.fact_of_the_day_quiz()
            elif choice == '10':
                print("\n👋 Thanks for exploring useless facts! Goodbye!")
                break
            else:
                print("❌ Invalid option. Please choose 1-10.")

### 4. Fact API Tester

class APITester:
    """Test and explore different API endpoints"""
    
    def __init__(self):
        self.api = UselessFactsAPI()
    
    def test_all_languages(self):
        """Test fact fetching in different languages"""
        print("\n🌍 TESTING MULTIPLE LANGUAGES")
        print("="*50)
        
        languages = ['en', 'de', 'es', 'fr', 'it', 'pt']
        
        for lang in languages:
            print(f"\n🔤 Language: {lang.upper()}")
            fact = self.api.get_random_fact(language=lang)
            if fact:
                print(f"   {fact['text']}")
            else:
                print(f"   ❌ No fact available in {lang}")
    
    def test_response_structure(self):
        """Examine the API response structure"""
        print("\n📋 EXAMINING API RESPONSE STRUCTURE")
        print("="*50)
        
        fact = self.api.get_random_fact()
        if fact:
            print("\n🔍 Response Keys:")
            for key in fact.keys():
                print(f"   - {key}: {type(fact[key]).__name__}")
            
            print("\n📊 Sample Data:")
            for key, value in fact.items():
                print(f"   {key}: {value}")
    
    def test_rate_limits(self):
        """Test API rate limits by making multiple requests"""
        print("\n⏱️ TESTING API PERFORMANCE")
        print("="*50)
        
        import time
        start_time = time.time()
        success_count = 0
        
        for i in range(5):
            fact = self.api.get_random_fact()
            if fact:
                success_count += 1
            time.sleep(0.2)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Success Rate: {success_count}/5")
        print(f"⏱️ Total Time: {elapsed:.2f} seconds")
        print(f"⚡ Average: {elapsed/5:.2f} seconds per request")

### 5. Fact Visualization

import matplotlib.pyplot as plt
from collections import Counter

class FactVisualizer:
    """Visualize fact statistics"""
    
    def __init__(self, api):
        self.api = api
    
    def create_category_chart(self):
        """Create a bar chart of fact categories"""
        if not self.api.category_counts:
            print("No data available for visualization.")
            return
        
        categories = list(self.api.category_counts.keys())
        counts = list(self.api.category_counts.values())
        
        plt.figure(figsize=(10, 6))
        plt.bar(categories, counts, color='skyblue', edgecolor='black')
        plt.title('Fact Categories Distribution', fontsize=16)
        plt.xlabel('Categories', fontsize=12)
        plt.ylabel('Number of Facts', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    def create_timeline(self):
        """Create a timeline of fact fetching"""
        if not self.api.fact_history:
            print("No history available.")
            return
        
        timestamps = [datetime.fromisoformat(f['timestamp']) 
                     for f in self.api.fact_history]
        
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, range(1, len(timestamps) + 1), 
                marker='o', linestyle='-', color='green')
        plt.title('Fact Fetching Timeline', fontsize=16)
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Cumulative Facts', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

### 6. Main Application Entry Point

def main():
    """Main entry point for the application"""
    app = FactDisplayApp()
    
    # Uncomment to run tests
    # tester = APITester()
    # tester.test_all_languages()
    # tester.test_response_structure()
    # tester.test_rate_limits()
    
    # Uncomment for visualization
    # visualizer = FactVisualizer(app.api)
    # visualizer.create_category_chart()
    
    # Run the main application
    app.run()

if __name__ == "__main__":
    main()