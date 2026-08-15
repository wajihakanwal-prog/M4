import requests
import json
import random
import time
from datetime import datetime

class TriviaQuiz:
    def __init__(self):
        self.base_url = "https://opentdb.com/api.php"
        self.session = requests.Session()
        self.score = 0
        self.total_questions = 0
        self.question_history = []
        self.difficulty_levels = ['easy', 'medium', 'hard']
        self.categories = self.fetch_categories()
        
    def fetch_categories(self):
        """Fetch available trivia categories"""
        try:
            response = requests.get("https://opentdb.com/api_category.php")
            response.raise_for_status()
            data = response.json()
            return {cat['id']: cat['name'] for cat in data['trivia_categories']}
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return {}
    
    def fetch_questions(self, amount=5, category=None, difficulty=None, type='multiple'):
        """
        Fetch trivia questions from Open Trivia Database
        
        Parameters:
        - amount: Number of questions (1-50)
        - category: Category ID (optional)
        - difficulty: 'easy', 'medium', 'hard' (optional)
        - type: 'multiple' or 'boolean'
        """
        params = {
            'amount': amount,
            'type': type,
            'encode': 'url3986'  # URL encoding for special characters
        }
        
        if category:
            params['category'] = category
        if difficulty:
            params['difficulty'] = difficulty
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['response_code'] == 0:
                return data['results']
            elif data['response_code'] == 1:
                print("No results found for the specified parameters")
                return []
            elif data['response_code'] == 2:
                print("Invalid parameter provided")
                return []
            elif data['response_code'] == 3:
                print("Session token not found")
                return []
            elif data['response_code'] == 4:
                print("Token exhausted - all questions answered")
                return []
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching questions: {e}")
            return []
    
    def decode_text(self, text):
        """Decode URL-encoded text"""
        from urllib.parse import unquote
        return unquote(text)
    
    def display_question(self, question_data, question_num, total):
        """Display a question and its options"""
        question = self.decode_text(question_data['question'])
        category = self.decode_text(question_data['category'])
        difficulty = question_data['difficulty'].upper()
        
        print("\n" + "="*70)
        print(f"📝 Question {question_num}/{total}")
        print(f"Category: {category}")
        print(f"Difficulty: {difficulty}")
        print("="*70)
        print(f"\n{question}\n")
        
        # Get options (for multiple choice)
        if question_data['type'] == 'multiple':
            options = question_data['incorrect_answers'] + [question_data['correct_answer']]
            random.shuffle(options)
            
            # Display options with letters
            for i, option in enumerate(options, 1):
                decoded_option = self.decode_text(option)
                letter = chr(64 + i)  # A, B, C, D
                print(f"   {letter}. {decoded_option}")
            
            return options
        else:
            # True/False questions
            print("   A. True")
            print("   B. False")
            return None
    
    def get_user_answer(self, question_type, options):
        """Get and validate user input"""
        while True:
            if question_type == 'multiple':
                answer = input("\nYour answer (A, B, C, D): ").strip().upper()
                if answer in ['A', 'B', 'C', 'D']:
                    index = ord(answer) - 65
                    if 0 <= index < len(options):
                        return options[index]
                    else:
                        print("❌ Invalid option. Please try again.")
                else:
                    print("❌ Please enter A, B, C, or D.")
            else:
                answer = input("\nYour answer (A for True, B for False): ").strip().upper()
                if answer in ['A', 'B']:
                    return answer == 'A'
                else:
                    print("❌ Please enter A or B.")
    
    def check_answer(self, user_answer, correct_answer):
        """Check if the answer is correct"""
        # Decode both answers for comparison
        if isinstance(correct_answer, bool):
            return user_answer == correct_answer
        else:
            user_decoded = self.decode_text(user_answer)
            correct_decoded = self.decode_text(correct_answer)
            return user_decoded == correct_decoded
    
    def run_quiz(self):
        """Main quiz loop"""
        print("\n" + "="*70)
        print("🎯 TRIVIA QUIZ GAME")
        print("="*70)
        
        # Get user preferences
        print("\n📊 Quiz Settings:")
        print("1. Easy")
        print("2. Medium")
        print("3. Hard")
        
        while True:
            try:
                diff_choice = int(input("\nSelect difficulty (1-3): "))
                if 1 <= diff_choice <= 3:
                    difficulty = self.difficulty_levels[diff_choice - 1]
                    break
                else:
                    print("Please enter a number between 1 and 3.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Number of questions
        while True:
            try:
                num_questions = int(input("Number of questions (1-20): "))
                if 1 <= num_questions <= 20:
                    break
                else:
                    print("Please enter a number between 1 and 20.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Fetch questions
        print(f"\n🔄 Fetching {num_questions} {difficulty} questions...")
        questions = self.fetch_questions(
            amount=num_questions,
            difficulty=difficulty,
            type='multiple'
        )
        
        if not questions:
            print("❌ No questions available. Please try again later.")
            return
        
        # Start quiz
        self.total_questions = len(questions)
        self.score = 0
        start_time = time.time()
        
        for i, q_data in enumerate(questions, 1):
            # Display question
            options = self.display_question(q_data, i, self.total_questions)
            
            # Get user answer
            user_answer = self.get_user_answer(q_data['type'], options)
            
            # Check answer
            correct_answer = q_data['correct_answer']
            is_correct = self.check_answer(user_answer, correct_answer)
            
            # Display result
            decoded_correct = self.decode_text(correct_answer)
            if is_correct:
                print("\n✅ Correct! 🎉")
                self.score += 1
            else:
                print(f"\n❌ Incorrect. The correct answer was: {decoded_correct}")
            
            # Store history
            self.question_history.append({
                'question': self.decode_text(q_data['question']),
                'user_answer': self.decode_text(str(user_answer)),
                'correct_answer': decoded_correct,
                'is_correct': is_correct
            })
            
            # Pause briefly
            time.sleep(0.5)
        
        # Show final results
        elapsed_time = time.time() - start_time
        self.show_results(elapsed_time)
    
    def show_results(self, elapsed_time):
        """Display final quiz results"""
        print("\n" + "="*70)
        print("🏆 QUIZ COMPLETE!")
        print("="*70)
        print(f"\nScore: {self.score}/{self.total_questions}")
        print(f"Percentage: {(self.score/self.total_questions)*100:.1f}%")
        
        # Calculate average time per question
        avg_time = elapsed_time / self.total_questions
        print(f"Total Time: {elapsed_time:.1f} seconds")
        print(f"Average Time per Question: {avg_time:.1f} seconds")
        
        # Grade
        percentage = (self.score / self.total_questions) * 100
        if percentage == 100:
            grade = "🌟 Perfect! You're a quiz master!"
        elif percentage >= 80:
            grade = "⭐ Excellent! Great job!"
        elif percentage >= 60:
            grade = "👍 Good! Keep practicing!"
        elif percentage >= 40:
            grade = "📚 Nice try! Review the answers below."
        else:
            grade = "💪 Keep learning! Don't give up!"
        
        print(f"\n{grade}")
        
        # Show question review
        print("\n📋 Question Review:")
        print("-"*70)
        for i, history in enumerate(self.question_history, 1):
            status = "✅" if history['is_correct'] else "❌"
            print(f"\n{status} Q{i}. {history['question']}")
            print(f"   Your answer: {history['user_answer']}")
            if not history['is_correct']:
                print(f"   Correct answer: {history['correct_answer']}")
    
    def play_again(self):
        """Ask if user wants to play again"""
        while True:
            choice = input("\n🔄 Play again? (yes/no): ").strip().lower()
            if choice in ['yes', 'y']:
                return True
            elif choice in ['no', 'n']:
                return False
            else:
                print("Please enter yes or no.")

### 3. Advanced Features: Custom Quiz Builder

class CustomQuizBuilder(TriviaQuiz):
    """Extended quiz with additional features"""
    
    def __init__(self):
        super().__init__()
        self.session_categories = None
        self.custom_questions = []
    
    def build_custom_quiz(self):
        """Build a custom quiz with specific categories"""
        print("\n" + "="*70)
        print("🔧 CUSTOM QUIZ BUILDER")
        print("="*70)
        
        # Display available categories
        print("\n📚 Available Categories:")
        for cat_id, cat_name in self.categories.items():
            print(f"   {cat_id}. {cat_name}")
        
        # Select category
        while True:
            try:
                category_id = int(input("\nEnter category ID (or 0 for random): "))
                if category_id == 0 or category_id in self.categories:
                    break
                else:
                    print("Invalid category ID. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Number of questions
        while True:
            try:
                num_questions = int(input("Number of questions (1-20): "))
                if 1 <= num_questions <= 20:
                    break
                else:
                    print("Please enter a number between 1 and 20.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Question type
        print("\nQuestion Type:")
        print("1. Multiple Choice")
        print("2. True/False")
        print("3. Mixed")
        
        while True:
            try:
                type_choice = int(input("Select type (1-3): "))
                if type_choice in [1, 2, 3]:
                    break
                else:
                    print("Please enter 1, 2, or 3.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Fetch questions
        cat_param = None if category_id == 0 else category_id
        type_param = 'multiple' if type_choice == 1 else 'boolean' if type_choice == 2 else None
        
        print(f"\n🔄 Fetching questions...")
        questions = self.fetch_questions(
            amount=num_questions,
            category=cat_param,
            type=type_param if type_param else 'multiple'
        )
        
        if not questions:
            # Try with different parameters if no results
            questions = self.fetch_questions(amount=num_questions, type='multiple')
        
        if not questions:
            print("❌ No questions available. Please try different settings.")
            return
        
        self.custom_questions = questions
        return questions
    
    def run_custom_quiz(self):
        """Run the custom quiz"""
        questions = self.build_custom_quiz()
        if not questions:
            return
        
        self.total_questions = len(questions)
        self.score = 0
        start_time = time.time()
        
        for i, q_data in enumerate(questions, 1):
            options = self.display_question(q_data, i, self.total_questions)
            user_answer = self.get_user_answer(q_data['type'], options)
            is_correct = self.check_answer(user_answer, q_data['correct_answer'])
            
            if is_correct:
                print("\n✅ Correct! 🎉")
                self.score += 1
            else:
                correct = self.decode_text(q_data['correct_answer'])
                print(f"\n❌ Incorrect. Correct answer: {correct}")
            
            self.question_history.append({
                'question': self.decode_text(q_data['question']),
                'user_answer': self.decode_text(str(user_answer)),
                'correct_answer': self.decode_text(q_data['correct_answer']),
                'is_correct': is_correct
            })
            
            time.sleep(0.5)
        
        elapsed_time = time.time() - start_time
        self.show_results(elapsed_time)

### 4. Quiz Statistics and Analysis


class QuizAnalytics:
    """Track and analyze quiz performance"""
    
    def __init__(self):
        self.history = []
        self.session_data = {
            'total_questions': 0,
            'correct_answers': 0,
            'categories_attempted': {},
            'difficulty_performance': {'easy': 0, 'medium': 0, 'hard': 0}
        }
    
    def log_question(self, question_data, is_correct, user_answer):
        """Log question attempt"""
        self.history.append({
            'timestamp': datetime.now(),
            'category': question_data.get('category', 'Unknown'),
            'difficulty': question_data.get('difficulty', 'medium'),
            'is_correct': is_correct,
            'user_answer': user_answer,
            'correct_answer': question_data.get('correct_answer')
        })
        
        # Update session data
        self.session_data['total_questions'] += 1
        if is_correct:
            self.session_data['correct_answers'] += 1
        
        category = question_data.get('category', 'Unknown')
        if category not in self.session_data['categories_attempted']:
            self.session_data['categories_attempted'][category] = {'correct': 0, 'total': 0}
        self.session_data['categories_attempted'][category]['total'] += 1
        if is_correct:
            self.session_data['categories_attempted'][category]['correct'] += 1
        
        difficulty = question_data.get('difficulty', 'medium')
        self.session_data['difficulty_performance'][difficulty] += 1 if is_correct else 0
    
    def get_statistics(self):
        """Generate comprehensive statistics"""
        stats = {
            'total_questions': self.session_data['total_questions'],
            'correct_answers': self.session_data['correct_answers'],
            'success_rate': (self.session_data['correct_answers'] / max(1, self.session_data['total_questions'])) * 100,
            'category_performance': {},
            'difficulty_analysis': {},
            'streak_count': 0
        }
        
        # Calculate category performance
        for category, data in self.session_data['categories_attempted'].items():
            if data['total'] > 0:
                stats['category_performance'][category] = {
                    'correct': data['correct'],
                    'total': data['total'],
                    'rate': (data['correct'] / data['total']) * 100
                }
        
        # Calculate difficulty performance
        for diff, correct_count in self.session_data['difficulty_performance'].items():
            total = sum(1 for q in self.history if q['difficulty'] == diff)
            if total > 0:
                stats['difficulty_analysis'][diff] = {
                    'correct': correct_count,
                    'total': total,
                    'rate': (correct_count / total) * 100
                }
        
        # Calculate current streak
        streak = 0
        for entry in reversed(self.history):
            if entry['is_correct']:
                streak += 1
            else:
                break
        stats['streak_count'] = streak
        
        return stats
    
    def display_statistics(self):
        """Display statistics in a readable format"""
        stats = self.get_statistics()
        
        print("\n" + "="*70)
        print("📊 QUIZ STATISTICS")
        print("="*70)
        print(f"\nTotal Questions Attempted: {stats['total_questions']}")
        print(f"Correct Answers: {stats['correct_answers']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Current Streak: {stats['streak_count']} 🏆")
        
        # Category performance
        if stats['category_performance']:
            print("\n📚 Category Performance:")
            for category, data in stats['category_performance'].items():
                print(f"   {category[:30]}: {data['rate']:.1f}% ({data['correct']}/{data['total']})")
        
        # Difficulty analysis
        if stats['difficulty_analysis']:
            print("\n⚡ Difficulty Analysis:")
            for difficulty, data in stats['difficulty_analysis'].items():
                print(f"   {difficulty.capitalize()}: {data['rate']:.1f}% ({data['correct']}/{data['total']})")

### 5. Main Application with Menu

def main():
    """Main application entry point"""
    quiz_app = CustomQuizBuilder()
    analytics = QuizAnalytics()
    
    print("\n" + "🎯"*35)
    print("   WELCOME TO TRIVIA QUIZ MASTER")
    print("🎯"*35)
    
    while True:
        print("\n" + "="*70)
        print("MAIN MENU")
        print("="*70)
        print("1. 🎲 Start Standard Quiz")
        print("2. 🔧 Build Custom Quiz")
        print("3. 📊 View Statistics")
        print("4. 🎯 Play Random Quiz")
        print("5. 🏆 Challenge Mode (Mixed Difficulty)")
        print("6. ❌ Quit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            # Standard quiz
            quiz_app.run_quiz()
            
            # Log results
            for q_data in quiz_app.question_history:
                analytics.log_question(
                    {'category': q_data['question'], 'difficulty': 'mixed'},
                    q_data['is_correct'],
                    q_data['user_answer']
                )
            
            if not quiz_app.play_again():
                break
        
        elif choice == '2':
            # Custom quiz
            quiz_app.run_custom_quiz()
            if not quiz_app.play_again():
                break
        
        elif choice == '3':
            # View statistics
            analytics.display_statistics()
        
        elif choice == '4':
            # Random quiz
            print("\n🎯 Random Quiz Mode")
            questions = quiz_app.fetch_questions(amount=10)
            if questions:
                quiz_app.total_questions = 10
                quiz_app.score = 0
                start_time = time.time()
                
                for i, q_data in enumerate(questions, 1):
                    options = quiz_app.display_question(q_data, i, 10)
                    user_answer = quiz_app.get_user_answer(q_data['type'], options)
                    is_correct = quiz_app.check_answer(user_answer, q_data['correct_answer'])
                    
                    if is_correct:
                        print("\n✅ Correct! 🎉")
                        quiz_app.score += 1
                    else:
                        correct = quiz_app.decode_text(q_data['correct_answer'])
                        print(f"\n❌ Incorrect. Correct: {correct}")
                    
                    quiz_app.question_history.append({
                        'question': quiz_app.decode_text(q_data['question']),
                        'user_answer': quiz_app.decode_text(str(user_answer)),
                        'correct_answer': quiz_app.decode_text(q_data['correct_answer']),
                        'is_correct': is_correct
                    })
                    
                    # Log to analytics
                    analytics.log_question(q_data, is_correct, user_answer)
                    
                    time.sleep(0.3)
                
                elapsed = time.time() - start_time
                quiz_app.show_results(elapsed)
            
            if not quiz_app.play_again():
                break
        
        elif choice == '5':
            # Challenge mode - mix of difficulties
            print("\n🏆 Challenge Mode")
            print("You'll get questions of mixed difficulty!")
            
            # Fetch questions from different difficulties
            all_questions = []
            for difficulty in ['easy', 'medium', 'hard']:
                questions = quiz_app.fetch_questions(amount=4, difficulty=difficulty)
                if questions:
                    all_questions.extend(questions)
            
            if all_questions:
                random.shuffle(all_questions)
                all_questions = all_questions[:12]  # Limit to 12 questions
                
                quiz_app.total_questions = len(all_questions)
                quiz_app.score = 0
                start_time = time.time()
                
                for i, q_data in enumerate(all_questions, 1):
                    options = quiz_app.display_question(q_data, i, len(all_questions))
                    user_answer = quiz_app.get_user_answer(q_data['type'], options)
                    is_correct = quiz_app.check_answer(user_answer, q_data['correct_answer'])
                    
                    if is_correct:
                        print("\n✅ Correct! 🎉")
                        quiz_app.score += 1
                    else:
                        correct = quiz_app.decode_text(q_data['correct_answer'])
                        print(f"\n❌ Incorrect. Correct: {correct}")
                    
                    quiz_app.question_history.append({
                        'question': quiz_app.decode_text(q_data['question']),
                        'user_answer': quiz_app.decode_text(str(user_answer)),
                        'correct_answer': quiz_app.decode_text(q_data['correct_answer']),
                        'is_correct': is_correct
                    })
                    
                    # Log to analytics
                    analytics.log_question(q_data, is_correct, user_answer)
                    
                    time.sleep(0.3)
                
                elapsed = time.time() - start_time
                quiz_app.show_results(elapsed)
            
            if not quiz_app.play_again():
                break
        
        elif choice == '6':
            print("\n👋 Thanks for playing! Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please choose 1-6.")

if __name__ == "__main__":
    main()
   
import unittest

class TestTriviaQuiz(unittest.TestCase):
    def setUp(self):
        self.quiz = TriviaQuiz()
    
    def test_fetch_questions(self):
        """Test fetching questions from API"""
        questions = self.quiz.fetch_questions(amount=5)
        self.assertIsNotNone(questions)
        self.assertTrue(len(questions) <= 5)
    
    def test_decode_text(self):
        """Test URL decoding"""
        encoded = "What%20is%20the%20capital%20of%20France%3F"
        decoded = self.quiz.decode_text(encoded)
        self.assertEqual(decoded, "What is the capital of France?")
    
    def test_question_display(self):
        """Test question display format"""
        question_data = {
            'question': 'Test question?',
            'category': 'Science',
            'difficulty': 'easy',
            'type': 'multiple',
            'incorrect_answers': ['Answer 1', 'Answer 2'],
            'correct_answer': 'Correct Answer'
        }
        options = self.quiz.display_question(question_data, 1, 10)
        self.assertIsNotNone(options)
        self.assertTrue(len(options) == 3)

# Run tests
if __name__ == "__main__":
    unittest.main()