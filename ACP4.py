import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

class HuggingFaceSentimentAnalyzer:
    """Sentiment analysis using Hugging Face Inference API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize the sentiment analyzer
        
        Args:
            api_key: Hugging Face API key (optional for free tier)
            model: Model to use for sentiment analysis
        """
        self.api_key = api_key
        self.model = model
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.history = []
        
        # Cache for results
        self.cache = {}
        self.cache_size = 100
        
        # Statistics
        self.stats = {
            'total_analyzed': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'errors': 0
        }
        
        print(f"✅ Sentiment Analyzer initialized with model: {model}")
        print(f"🔑 API Key: {'Loaded' if api_key else 'Not provided (using free tier)'}")
    
    def analyze_text(self, text: str, use_cache: bool = True) -> Dict:
        """
        Analyze sentiment of a text
        
        Args:
            text: Text to analyze
            use_cache: Whether to use cached results
        
        Returns:
            Dictionary with sentiment analysis results
        """
        if not text or not text.strip():
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'error': 'Empty text',
                'timestamp': datetime.now().isoformat()
            }
        
        # Check cache
        cache_key = text.strip().lower()
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Prepare the request
            payload = {"inputs": text}
            
            # Make API request
            if self.api_key:
                response = requests.post(self.api_url, headers=self.headers, json=payload)
            else:
                # Free tier with rate limiting
                time.sleep(0.1)  # Avoid rate limiting
                response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                sentiment_data = self._process_response(result, text)
            elif response.status_code == 503:
                # Model is loading, wait and retry
                wait_time = 5
                print(f"⏳ Model loading, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
                response = requests.post(self.api_url, headers=self.headers, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    sentiment_data = self._process_response(result, text)
                else:
                    sentiment_data = self._handle_error(text, response)
            else:
                sentiment_data = self._handle_error(text, response)
            
            # Cache the result
            if use_cache and 'error' not in sentiment_data:
                if len(self.cache) >= self.cache_size:
                    # Remove oldest entry
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                self.cache[cache_key] = sentiment_data
            
            # Update statistics
            self._update_stats(sentiment_data)
            
            # Store history
            self.history.append(sentiment_data)
            
            return sentiment_data
            
        except Exception as e:
            error_result = {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.stats['errors'] += 1
            return error_result
    
    def _process_response(self, response_data: List[Dict], text: str) -> Dict:
        """Process the API response"""
        try:
            if isinstance(response_data, list) and len(response_data) > 0:
                result = response_data[0]
                
                # For models that return label and score
                if 'label' in result and 'score' in result:
                    label = result['label']
                    score = result['score']
                    
                    # Map to sentiment categories
                    if 'POSITIVE' in label.upper():
                        sentiment = 'positive'
                    elif 'NEGATIVE' in label.upper():
                        sentiment = 'negative'
                    else:
                        sentiment = 'neutral'
                    
                    return {
                        'text': text,
                        'sentiment': sentiment,
                        'label': label,
                        'score': score,
                        'confidence': f"{score * 100:.2f}%",
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Alternative response format
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'raw_response': response_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'error': f'Processing error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _handle_error(self, text: str, response) -> Dict:
        """Handle API errors"""
        error_msg = f"API Error (Status: {response.status_code})"
        if response.text:
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg = error_data['error']
            except:
                pass
        
        return {
            'text': text,
            'sentiment': 'neutral',
            'score': 0.0,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
    
    def _update_stats(self, result: Dict):
        """Update statistics"""
        self.stats['total_analyzed'] += 1
        if 'error' in result:
            self.stats['errors'] += 1
        else:
            sentiment = result.get('sentiment', 'neutral')
            if sentiment == 'positive':
                self.stats['positive'] += 1
            elif sentiment == 'negative':
                self.stats['negative'] += 1
            else:
                self.stats['neutral'] += 1
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts"""
        results = []
        for text in texts:
            result = self.analyze_text(text)
            results.append(result)
            # Small delay between requests
            if len(texts) > 1:
                time.sleep(0.05)
        return results
    
    def get_sentiment_distribution(self) -> Dict:
        """Get sentiment distribution statistics"""
        total = self.stats['total_analyzed'] - self.stats['errors']
        if total == 0:
            return {'total': 0, 'distribution': {}}
        
        return {
            'total': total,
            'positive': self.stats['positive'],
            'negative': self.stats['negative'],
            'neutral': self.stats['neutral'],
            'positive_percentage': (self.stats['positive'] / total) * 100,
            'negative_percentage': (self.stats['negative'] / total) * 100,
            'neutral_percentage': (self.stats['neutral'] / total) * 100,
            'errors': self.stats['errors']
        }
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        dist = self.get_sentiment_distribution()
        return {
            **dist,
            'total_analyzed': self.stats['total_analyzed'],
            'cache_size': len(self.cache),
            'history_size': len(self.history),
            'model': self.model
        }
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        print("🗑️ Cache cleared")
    
    def clear_history(self):
        """Clear history"""
        self.history.clear()
        print("📜 History cleared")

### 3. Local Model Implementation


from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

class LocalSentimentAnalyzer:
    """Sentiment analysis using local Hugging Face models"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize local sentiment analyzer
        
        Args:
            model_name: Name of the Hugging Face model
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sentiment_pipeline = None
        self.history = []
        self.stats = {
            'total_analyzed': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        self._load_model()
    
    def _load_model(self):
        """Load the sentiment analysis model locally"""
        try:
            print(f"🔄 Loading model: {self.model_name}")
            print(f"📱 Using device: {self.device}")
            
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1
            )
            
            print("✅ Model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("🔄 Trying fallback model...")
            try:
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=0 if self.device == "cuda" else -1
                )
                print("✅ Fallback model loaded!")
            except Exception as e2:
                print(f"❌ Failed to load any model: {e2}")
                self.sentiment_pipeline = None
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze sentiment using local model"""
        if not text or not text.strip():
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'error': 'Empty text',
                'timestamp': datetime.now().isoformat()
            }
        
        if not self.sentiment_pipeline:
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'error': 'Model not loaded',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            result = self.sentiment_pipeline(text)[0]
            
            label = result['label']
            score = result['score']
            
            # Map to sentiment categories
            if 'POSITIVE' in label.upper():
                sentiment = 'positive'
            elif 'NEGATIVE' in label.upper():
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            analysis_result = {
                'text': text,
                'sentiment': sentiment,
                'label': label,
                'score': score,
                'confidence': f"{score * 100:.2f}%",
                'timestamp': datetime.now().isoformat()
            }
            
            # Update stats
            self._update_stats(analysis_result)
            self.history.append(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_stats(self, result: Dict):
        """Update statistics"""
        self.stats['total_analyzed'] += 1
        sentiment = result.get('sentiment', 'neutral')
        if sentiment == 'positive':
            self.stats['positive'] += 1
        elif sentiment == 'negative':
            self.stats['negative'] += 1
        else:
            self.stats['neutral'] += 1
    
    def get_statistics(self) -> Dict:
        """Get statistics"""
        total = self.stats['total_analyzed']
        if total == 0:
            return {'total': 0}
        
        return {
            'total_analyzed': total,
            'positive': self.stats['positive'],
            'negative': self.stats['negative'],
            'neutral': self.stats['neutral'],
            'positive_percentage': (self.stats['positive'] / total) * 100,
            'negative_percentage': (self.stats['negative'] / total) * 100,
            'neutral_percentage': (self.stats['neutral'] / total) * 100
        }

### 4. Enhanced Sentiment Analyzer with Multiple Models


class MultiModelSentimentAnalyzer:
    """Sentiment analyzer using multiple models for comparison"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.models = {
            'distilbert': {
                'name': 'DistilBERT',
                'model': 'distilbert-base-uncased-finetuned-sst-2-english',
                'analyzer': HuggingFaceSentimentAnalyzer(api_key, 'distilbert-base-uncased-finetuned-sst-2-english')
            },
            'roberta': {
                'name': 'RoBERTa',
                'model': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                'analyzer': HuggingFaceSentimentAnalyzer(api_key, 'cardiffnlp/twitter-roberta-base-sentiment-latest')
            }
        }
        self.results_cache = {}
    
    def analyze_with_all(self, text: str) -> Dict:
        """Analyze sentiment with all models"""
        results = {}
        
        for model_key, model_data in self.models.items():
            try:
                result = model_data['analyzer'].analyze_text(text)
                results[model_key] = {
                    'sentiment': result.get('sentiment', 'neutral'),
                    'confidence': result.get('confidence', '0%'),
                    'score': result.get('score', 0.0),
                    'label': result.get('label', ''),
                    'error': result.get('error')
                }
            except Exception as e:
                results[model_key] = {
                    'sentiment': 'neutral',
                    'error': str(e)
                }
        
        # Calculate consensus
        sentiment_votes = {}
        for model_key, result in results.items():
            if 'error' not in result:
                sentiment = result['sentiment']
                sentiment_votes[sentiment] = sentiment_votes.get(sentiment, 0) + 1
        
        consensus = {
            'majority_sentiment': max(sentiment_votes.items(), key=lambda x: x[1])[0] if sentiment_votes else 'neutral',
            'agreement': (max(sentiment_votes.values()) / len(self.models)) * 100 if sentiment_votes else 0,
            'votes': sentiment_votes
        }
        
        return {
            'text': text,
            'results': results,
            'consensus': consensus,
            'timestamp': datetime.now().isoformat()
        }
    
    def display_comparison(self, comparison_results: Dict):
        """Display model comparison results"""
        if not comparison_results:
            return
        
        print("\n" + "="*70)
        print("🤖 MULTI-MODEL SENTIMENT ANALYSIS")
        print("="*70)
        print(f"\n📝 Text: {comparison_results['text']}")
        
        print(f"\n📊 Model Results:")
        print("-"*50)
        
        for model_key, result in comparison_results['results'].items():
            model_name = self.models[model_key]['name']
            
            if 'error' in result:
                status = f"❌ Error: {result['error']}"
            else:
                emoji = self._get_sentiment_emoji(result['sentiment'])
                status = f"{emoji} {result['sentiment'].upper()} (Confidence: {result.get('confidence', 'N/A')})"
            
            print(f"   {model_name}: {status}")
        
        # Consensus
        consensus = comparison_results['consensus']
        print(f"\n🎯 Consensus: {consensus['majority_sentiment'].upper()}")
        print(f"📊 Agreement: {consensus['agreement']:.1f}%")
        print(f"🔄 Votes: {json.dumps(consensus['votes'])}")
        
        print("="*70)
    
    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment"""
        emojis = {
            'positive': '😊',
            'negative': '😞',
            'neutral': '😐'
        }
        return emojis.get(sentiment, '🤔')

### 5. Interactive Application


class SentimentAnalysisApp:
    """Interactive sentiment analysis application"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.analyzer = HuggingFaceSentimentAnalyzer(self.api_key)
        self.local_analyzer = LocalSentimentAnalyzer()
        self.multi_analyzer = MultiModelSentimentAnalyzer(self.api_key)
        
    def _get_api_key(self) -> Optional[str]:
        """Get API key from user or environment"""
        # Try to get from environment variable
        import os
        api_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        
        if not api_key:
            print("\n🔑 Do you have a Hugging Face API key?")
            print("   (Free tier available at huggingface.co/settings/tokens)")
            response = input("   Enter API key (or press Enter to continue without): ").strip()
            if response:
                api_key = response
        
        return api_key if api_key else None
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "💭"*35)
        print("   SENTIMENT ANALYSIS TOOL")
        print("   Powered by Hugging Face 🤗")
        print("💭"*35)
        print("\n📌 Analyze text sentiment in real-time:")
        print("   - Positive 😊  - Negative 😞  - Neutral 😐")
        print("\n" + "-"*70)
    
    def display_menu(self):
        """Display main menu"""
        print("\n📋 MAIN MENU")
        print("-"*50)
        print("1. 📊 Analyze Single Text")
        print("2. 📚 Batch Analyze")
        print("3. 📈 View Statistics")
        print("4. 📜 View History")
        print("5. 🤖 Multi-Model Comparison")
        print("6. 📱 Local Model Analysis")
        print("7. 🎯 Sentiment Trend Analysis")
        print("8. 💾 Export Results")
        print("9. 🧪 Test with Samples")
        print("10. ❌ Exit")
        print("-"*50)
    
    def analyze_single(self):
        """Analyze a single text"""
        print("\n📝 Enter text to analyze:")
        print("   (Type 'quit' to go back)")
        
        while True:
            text = input("\n>> ").strip()
            if text.lower() == 'quit':
                break
            
            if not text:
                print("⚠️ Please enter some text.")
                continue
            
            print("\n🔄 Analyzing...")
            result = self.analyzer.analyze_text(text)
            self._display_result(result)
            
            # Ask for more detailed analysis
            if 'error' not in result:
                self._offer_advanced_analysis(text)
    
    def _display_result(self, result: Dict):
        """Display analysis result"""
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            return
        
        sentiment = result['sentiment']
        emoji = self._get_sentiment_emoji(sentiment)
        label = result.get('label', 'N/A')
        confidence = result.get('confidence', '0%')
        
        print("\n" + "="*60)
        print("📊 SENTIMENT ANALYSIS RESULT")
        print("="*60)
        print(f"\n📝 Text: {result['text']}")
        print(f"🎯 Sentiment: {emoji} {sentiment.upper()}")
        print(f"🏷️  Label: {label}")
        print(f"📊 Confidence: {confidence}")
        print(f"📅 Time: {result.get('timestamp', 'Unknown')}")
        
        # Additional context
        if sentiment == 'positive':
            print("\n💡 The text expresses positive sentiment.")
        elif sentiment == 'negative':
            print("\n💡 The text expresses negative sentiment.")
        else:
            print("\n💡 The text expresses neutral sentiment.")
        
        print("="*60)
    
    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment"""
        emojis = {
            'positive': '😊',
            'negative': '😞',
            'neutral': '😐'
        }
        return emojis.get(sentiment, '🤔')
    
    def _offer_advanced_analysis(self, text: str):
        """Offer advanced analysis options"""
        print("\n🔧 Advanced options:")
        print("1. Analyze with local model")
        print("2. Multi-model comparison")
        print("3. Back to main menu")
        
        choice = input("\nSelect option (1-3): ").strip()
        if choice == '1':
            result = self.local_analyzer.analyze_text(text)
            self._display_result(result)
        elif choice == '2':
            results = self.multi_analyzer.analyze_with_all(text)
            self.multi_analyzer.display_comparison(results)
    
    def batch_analyze(self):
        """Analyze multiple texts"""
        print("\n📚 Batch Analysis")
        print("Enter multiple texts (one per line).")
        print("Press Enter twice to finish.")
        
        texts = []
        print("\nEnter texts:")
        while True:
            line = input().strip()
            if not line and texts:
                break
            if line:
                texts.append(line)
        
        if not texts:
            print("No texts entered.")
            return
        
        print(f"\n🔄 Analyzing {len(texts)} texts...")
        results = self.analyzer.analyze_batch(texts)
        
        # Display results
        print("\n" + "="*60)
        print("📊 BATCH ANALYSIS RESULTS")
        print("="*60)
        
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0, 'errors': 0}
        
        for i, result in enumerate(results, 1):
            if 'error' in result:
                status = "❌ ERROR"
                sentiment_counts['errors'] += 1
            else:
                emoji = self._get_sentiment_emoji(result['sentiment'])
                status = f"{emoji} {result['sentiment'].upper()}"
                sentiment_counts[result['sentiment']] += 1
            
            print(f"\n{i}. {result['text'][:50]}...")
            print(f"   → {status} (Confidence: {result.get('confidence', 'N/A')})")
        
        # Summary
        print("\n" + "-"*60)
        print("📊 SUMMARY:")
        total_valid = len(texts) - sentiment_counts['errors']
        print(f"   ✅ Valid: {total_valid}")
        for sentiment, count in sentiment_counts.items():
            if sentiment != 'errors':
                percentage = (count / max(1, total_valid)) * 100
                print(f"   {sentiment.capitalize()}: {count} ({percentage:.1f}%)")
        if sentiment_counts['errors'] > 0:
            print(f"   ❌ Errors: {sentiment_counts['errors']}")
        print("="*60)
    
    def view_statistics(self):
        """Display statistics"""
        stats = self.analyzer.get_statistics()
        
        print("\n" + "="*60)
        print("📊 SENTIMENT ANALYSIS STATISTICS")
        print("="*60)
        
        print(f"\n📌 Model: {stats.get('model', 'Unknown')}")
        print(f"\n📊 Total Analyzed: {stats['total_analyzed']}")
        
        if stats['total_analyzed'] > 0:
            print(f"\n📈 Sentiment Distribution:")
            print(f"   😊 Positive: {stats['positive']} ({stats['positive_percentage']:.1f}%)")
            print(f"   😞 Negative: {stats['negative']} ({stats['negative_percentage']:.1f}%)")
            print(f"   😐 Neutral: {stats['neutral']} ({stats['neutral_percentage']:.1f}%)")
            print(f"   ❌ Errors: {stats['errors']}")
        
        print(f"\n💾 Cache Size: {stats.get('cache_size', 0)}")
        print(f"📜 History Size: {stats.get('history_size', 0)}")
        print("="*60)
    
    def view_history(self):
        """View analysis history"""
        if not self.analyzer.history:
            print("\n📜 No history available.")
            return
        
        print("\n" + "="*60)
        print("📜 ANALYSIS HISTORY")
        print("="*60)
        
        # Show last 15 entries
        history = self.analyzer.history[-15:]
        
        for entry in history:
            if 'error' in entry:
                status = "❌ ERROR"
            else:
                emoji = self._get_sentiment_emoji(entry['sentiment'])
                status = f"{emoji} {entry['sentiment'].upper()}"
            
            print(f"\n📅 {entry.get('timestamp', 'Unknown')[:19]}")
            print(f"📝 {entry['text'][:60]}")
            print(f"   → {status}")
            if 'confidence' in entry:
                print(f"   Confidence: {entry['confidence']}")
            print("-"*50)
    
    def multi_model_analysis(self):
        """Run multi-model comparison"""
        print("\n🤖 Multi-Model Sentiment Analysis")
        text = input("\nEnter text to analyze with all models: ").strip()
        
        if not text:
            print("No text entered.")
            return
        
        print("\n🔄 Analyzing with multiple models...")
        results = self.multi_analyzer.analyze_with_all(text)
        self.multi_analyzer.display_comparison(results)
    
    def trend_analysis(self):
        """Analyze sentiment trends over time"""
        if not self.analyzer.history:
            print("\n📊 No data for trend analysis.")
            print("Analyze some texts first!")
            return
        
        print("\n" + "="*60)
        print("📈 SENTIMENT TREND ANALYSIS")
        print("="*60)
        
        # Analyze history
        sentiment_over_time = []
        for entry in self.analyzer.history:
            if 'error' not in entry:
                sentiment_over_time.append({
                    'timestamp': datetime.fromisoformat(entry['timestamp']),
                    'sentiment': entry['sentiment']
                })
        
        if not sentiment_over_time:
            print("No valid sentiment data available.")
            return
        
        # Calculate trends
        total = len(sentiment_over_time)
        positive = sum(1 for s in sentiment_over_time if s['sentiment'] == 'positive')
        negative = sum(1 for s in sentiment_over_time if s['sentiment'] == 'negative')
        neutral = sum(1 for s in sentiment_over_time if s['sentiment'] == 'neutral')
        
        print(f"\n📊 Overall Sentiment Distribution (Last {total} analyses):")
        print(f"   😊 Positive: {positive} ({positive/total*100:.1f}%)")
        print(f"   😞 Negative: {negative} ({negative/total*100:.1f}%)")
        print(f"   😐 Neutral: {neutral} ({neutral/total*100:.1f}%)")
        
        # Recent trend
        recent = sentiment_over_time[-5:] if len(sentiment_over_time) >= 5 else sentiment_over_time
        recent_positive = sum(1 for s in recent if s['sentiment'] == 'positive')
        
        if len(sentiment_over_time) >= 10:
            print(f"\n📈 Recent Trend (Last 5):")
            print(f"   {'😊' if recent_positive >= 3 else '😐'} Mostly {'positive' if recent_positive >= 3 else 'neutral/negative'}")
        
        # Sentiment score (simplified)
        score = (positive - negative) / total * 100
        print(f"\n📊 Sentiment Score: {score:.1f}%")
        if score > 30:
            print("   🌟 Overall positive sentiment")
        elif score < -30:
            print("   ⚠️ Overall negative sentiment")
        else:
            print("   😐 Overall neutral sentiment")
        
        print("="*60)
    
    def export_results(self):
        """Export analysis results"""
        if not self.analyzer.history:
            print("\n📁 No data to export.")
            return
        
        filename = f"sentiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'model': self.analyzer.model,
                'statistics': self.analyzer.get_statistics(),
                'history': self.analyzer.history
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Results exported to '{filename}'")
            print(f"📁 Contains {len(self.analyzer.history)} analyzed texts")
            
        except Exception as e:
            print(f"❌ Error exporting results: {e}")
    
    def test_samples(self):
        """Test with sample texts"""
        sample_texts = [
            "I absolutely love this product! It's amazing! 😊",
            "This is the worst experience I've ever had. Terrible service.",
            "The weather today is okay, nothing special.",
            "I'm so happy with the results! Highly recommend!",
            "This movie was a complete waste of time. Boring.",
            "The food was decent, but the service could be better.",
            "Best day ever! Everything went perfectly!",
            "I'm feeling really frustrated with this situation."
        ]
        
        print("\n🧪 TESTING WITH SAMPLE TEXTS")
        print("="*60)
        
        for i, text in enumerate(sample_texts, 1):
            result = self.analyzer.analyze_text(text)
            emoji = self._get_sentiment_emoji(result.get('sentiment', 'neutral'))
            
            print(f"\n{i}. {text}")
            print(f"   → {emoji} {result.get('sentiment', 'neutral').upper()}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
        
        print("\n" + "="*60)
        print("📊 Sample Analysis Complete!")
        
        # Show distribution
        stats = self.analyzer.get_sentiment_distribution()
        print(f"\nDistribution of samples:")
        print(f"   Positive: {stats.get('positive', 0)}")
        print(f"   Negative: {stats.get('negative', 0)}")
        print(f"   Neutral: {stats.get('neutral', 0)}")
    
    def run(self):
        """Main application loop"""
        self.display_welcome()
        
        while True:
            self.display_menu()
            choice = input("\nSelect option (1-10): ").strip()
            
            if choice == '1':
                self.analyze_single()
            elif choice == '2':
                self.batch_analyze()
            elif choice == '3':
                self.view_statistics()
            elif choice == '4':
                self.view_history()
            elif choice == '5':
                self.multi_model_analysis()
            elif choice == '6':
                print("\n📱 Local Model Analysis")
                text = input("Enter text: ").strip()
                if text:
                    result = self.local_analyzer.analyze_text(text)
                    self._display_result(result)
            elif choice == '7':
                self.trend_analysis()
            elif choice == '8':
                self.export_results()
            elif choice == '9':
                self.test_samples()
            elif choice == '10':
                print("\n👋 Thanks for using the Sentiment Analysis Tool!")
                print("💭 Keep analyzing and understanding text!")
                break
            else:
                print("❌ Invalid option. Please choose 1-10.")

### 6. Unit Tests


import unittest
from unittest.mock import patch, Mock

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = HuggingFaceSentimentAnalyzer()
    
    def test_analyze_positive(self):
        """Test positive sentiment analysis"""
        result = self.analyzer.analyze_text("I love this!")
        self.assertEqual(result['sentiment'], 'positive')
    
    def test_analyze_negative(self):
        """Test negative sentiment analysis"""
        result = self.analyzer.analyze_text("This is terrible!")
        self.assertEqual(result['sentiment'], 'negative')
    
    def test_analyze_neutral(self):
        """Test neutral sentiment analysis"""
        result = self.analyzer.analyze_text("The sky is blue.")
        self.assertEqual(result['sentiment'], 'neutral')
    
    def test_empty_text(self):
        """Test empty text handling"""
        result = self.analyzer.analyze_text("")
        self.assertIn('error', result)
    
    def test_batch_analysis(self):
        """Test batch analysis"""
        texts = ["Good", "Bad", "Okay"]
        results = self.analyzer.analyze_batch(texts)
        self.assertEqual(len(results), 3)
    
    def test_statistics(self):
        """Test statistics tracking"""
        self.analyzer.analyze_text("Great!")
        stats = self.analyzer.get_statistics()
        self.assertEqual(stats['total_analyzed'], 1)

if __name__ == "__main__":
    unittest.main()