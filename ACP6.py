import torch
from transformers import (
    PegasusForConditionalGeneration, 
    PegasusTokenizer,
    BartForConditionalGeneration,
    BartTokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer
)
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime
import re

class TextSummarizer:
    """Base class for text summarization with multiple models"""
    
    def __init__(self, model_name: str = "google/pegasus-xsum"):
        """
        Initialize the summarizer
        
        Args:
            model_name: Hugging Face model name
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.history = []
        self.stats = {
            'total_summarized': 0,
            'total_chars_input': 0,
            'total_chars_output': 0
        }
        
        # Load the model
        self.load_model()
        
        print(f"✅ Summarizer initialized with model: {model_name}")
        print(f"📱 Using device: {self.device}")
    
    def load_model(self):
        """Load the specified model and tokenizer"""
        try:
            # Determine model type and load accordingly
            if "pegasus" in self.model_name.lower():
                self.tokenizer = PegasusTokenizer.from_pretrained(self.model_name)
                self.model = PegasusForConditionalGeneration.from_pretrained(self.model_name)
            elif "bart" in self.model_name.lower():
                self.tokenizer = BartTokenizer.from_pretrained(self.model_name)
                self.model = BartForConditionalGeneration.from_pretrained(self.model_name)
            elif "t5" in self.model_name.lower():
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
                self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
            
            # Move to device
            self.model.to(self.device)
            print(f"✅ Model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
            self.tokenizer = None
    
    def summarize(
        self, 
        text: str, 
        max_length: int = 150, 
        min_length: int = 30,
        do_sample: bool = False,
        temperature: float = 0.7,
        num_beams: int = 4,
        length_penalty: float = 2.0,
        early_stopping: bool = True
    ) -> Dict:
        """
        Summarize a text with adjustable parameters
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            do_sample: Whether to use sampling
            temperature: Sampling temperature
            num_beams: Number of beams for beam search
            length_penalty: Length penalty exponent
            early_stopping: Whether to stop early
        
        Returns:
            Dictionary with summary and metadata
        """
        if not text or not text.strip():
            return {
                'error': 'Empty text provided',
                'summary': '',
                'timestamp': datetime.now().isoformat()
            }
        
        if not self.model or not self.tokenizer:
            return {
                'error': 'Model not loaded',
                'summary': '',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate summary
            start_time = time.time()
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=do_sample,
                    temperature=temperature,
                    num_beams=num_beams,
                    length_penalty=length_penalty,
                    early_stopping=early_stopping,
                    no_repeat_ngram_size=3
                )
            
            generation_time = time.time() - start_time
            
            # Decode the summary
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Calculate statistics
            result = {
                'text': text,
                'summary': summary,
                'input_length': len(text.split()),
                'output_length': len(summary.split()),
                'compression_ratio': len(summary) / len(text) if len(text) > 0 else 0,
                'generation_time': generation_time,
                'parameters': {
                    'max_length': max_length,
                    'min_length': min_length,
                    'do_sample': do_sample,
                    'temperature': temperature,
                    'num_beams': num_beams,
                    'length_penalty': length_penalty,
                    'early_stopping': early_stopping
                },
                'model': self.model_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update statistics
            self._update_stats(result)
            
            # Store history
            self.history.append(result)
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'summary': '',
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_stats(self, result: Dict):
        """Update statistics"""
        self.stats['total_summarized'] += 1
        self.stats['total_chars_input'] += len(result.get('text', ''))
        self.stats['total_chars_output'] += len(result.get('summary', ''))
    
    def get_statistics(self) -> Dict:
        """Get summarization statistics"""
        total = self.stats['total_summarized']
        if total == 0:
            return {'total_summarized': 0}
        
        avg_input = self.stats['total_chars_input'] / total
        avg_output = self.stats['total_chars_output'] / total
        avg_compression = avg_output / avg_input if avg_input > 0 else 0
        
        return {
            'total_summarized': total,
            'avg_input_length': avg_input,
            'avg_output_length': avg_output,
            'avg_compression_ratio': avg_compression,
            'total_chars_input': self.stats['total_chars_input'],
            'total_chars_output': self.stats['total_chars_output']
        }

### 3. Multi-Model Summarizer


class MultiModelSummarizer:
    """Summarizer with multiple model support"""
    
    def __init__(self):
        self.models = {}
        self.current_model = None
        self.available_models = {
            'pegasus_xsum': {
                'name': 'Pegasus (XSum)',
                'model': TextSummarizer('google/pegasus-xsum'),
                'description': 'Good for news articles and extreme summarization'
            },
            'pegasus_cnn': {
                'name': 'Pegasus (CNN)',
                'model': TextSummarizer('google/pegasus-cnn_dailymail'),
                'description': 'Good for news summarization'
            },
            'bart': {
                'name': 'BART',
                'model': TextSummarizer('facebook/bart-large-cnn'),
                'description': 'Balanced summarization for various texts'
            },
            't5_small': {
                'name': 'T5 Small',
                'model': TextSummarizer('t5-small'),
                'description': 'Faster, smaller model for quick summaries'
            }
        }
        
        # Load models (lazy loading)
        self.loaded_models = {}
        self.current_model_key = None
    
    def load_model(self, model_key: str) -> bool:
        """Load a specific model"""
        if model_key not in self.available_models:
            print(f"❌ Model '{model_key}' not found")
            return False
        
        if model_key not in self.loaded_models:
            print(f"🔄 Loading model: {model_key}")
            try:
                summarizer = self.available_models[model_key]['model']
                if summarizer.model:
                    self.loaded_models[model_key] = summarizer
                    self.current_model_key = model_key
                    print(f"✅ Model loaded: {model_key}")
                    return True
                else:
                    print(f"❌ Failed to load model: {model_key}")
                    return False
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                return False
        else:
            self.current_model_key = model_key
            return True
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available models"""
        return [
            {
                'key': key,
                'name': info['name'],
                'description': info['description'],
                'loaded': key in self.loaded_models
            }
            for key, info in self.available_models.items()
        ]
    
    def summarize_with_model(
        self, 
        model_key: str, 
        text: str,
        **kwargs
    ) -> Dict:
        """Summarize using a specific model"""
        if not self.load_model(model_key):
            return {'error': f'Model {model_key} not available'}
        
        summarizer = self.loaded_models[model_key]
        return summarizer.summarize(text, **kwargs)
    
    def summarize_with_all(self, text: str, **kwargs) -> Dict:
        """Summarize text with all available models"""
        results = {}
        
        print(f"\n🔄 Summarizing with multiple models...")
        print(f"📝 Input length: {len(text.split())} words")
        print("-" * 50)
        
        for model_key in self.available_models.keys():
            if self.load_model(model_key):
                print(f"🔄 Using {model_key}...")
                result = self.summarize_with_model(model_key, text, **kwargs)
                if 'error' in result:
                    results[model_key] = {'error': result['error']}
                else:
                    results[model_key] = {
                        'summary': result['summary'],
                        'length': len(result['summary'].split()),
                        'time': result.get('generation_time', 0)
                    }
                    print(f"   ✅ Generated {len(result['summary'].split())} words in {result.get('generation_time', 0):.2f}s")
        
        return results
    
    def display_comparison(self, results: Dict, text: str):
        """Display comparison of different models"""
        print("\n" + "="*80)
        print("📊 MODEL COMPARISON")
        print("="*80)
        print(f"\n📝 Original Text ({len(text.split())} words):")
        print("-"*50)
        print(text[:300] + "..." if len(text) > 300 else text)
        print("-"*50)
        
        print("\n📋 Summaries:")
        print("="*80)
        
        for model_key, result in results.items():
            model_name = self.available_models.get(model_key, {}).get('name', model_key)
            
            if 'error' in result:
                print(f"\n❌ {model_name}: Error - {result['error']}")
            else:
                print(f"\n🔹 {model_name}:")
                print(f"   Length: {result['length']} words")
                print(f"   Time: {result['time']:.2f}s")
                print(f"   Summary: {result['summary']}")
            
            print("-"*50)

### 4. Advanced Summarizer with Custom Parameters

class AdvancedSummarizer:
    """Advanced summarizer with parameter experimentation"""
    
    def __init__(self, model_key: str = 'pegasus_cnn'):
        self.model_key = model_key
        self.summarizer = TextSummarizer(
            'google/pegasus-cnn_dailymail' if 'pegasus' in model_key else 'facebook/bart-large-cnn'
        )
        self.experiment_history = []
    
    def summarize_with_parameters(
        self,
        text: str,
        param_sets: List[Dict] = None
    ) -> Dict:
        """
        Experiment with different parameter combinations
        
        Args:
            text: Text to summarize
            param_sets: List of parameter dictionaries
        
        Returns:
            Results of the experiments
        """
        if not param_sets:
            # Default parameter sets to experiment
            param_sets = [
                {'max_length': 50, 'min_length': 10, 'num_beams': 2},
                {'max_length': 100, 'min_length': 20, 'num_beams': 4},
                {'max_length': 150, 'min_length': 30, 'num_beams': 6},
                {'max_length': 200, 'min_length': 40, 'num_beams': 8},
                {'max_length': 250, 'min_length': 50, 'num_beams': 10},
            ]
        
        results = []
        print(f"\n🔬 Running summarization experiments...")
        print(f"📊 {len(param_sets)} parameter combinations")
        print("-"*60)
        
        for i, params in enumerate(param_sets, 1):
            print(f"\n🔹 Experiment {i}:")
            print(f"   Max Length: {params.get('max_length', 150)}")
            print(f"   Min Length: {params.get('min_length', 30)}")
            print(f"   Beams: {params.get('num_beams', 4)}")
            
            result = self.summarizer.summarize(text, **params)
            
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Summary length: {len(result['summary'].split())} words")
                print(f"   ⏱️  Time: {result.get('generation_time', 0):.2f}s")
                print(f"   📝 Compression ratio: {result.get('compression_ratio', 0):.2%}")
                
                results.append({
                    'parameters': params,
                    'summary': result['summary'],
                    'length': len(result['summary'].split()),
                    'time': result.get('generation_time', 0),
                    'compression_ratio': result.get('compression_ratio', 0)
                })
        
        self.experiment_history.append({
            'text': text,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
        return results
    
    def display_parameter_comparison(self, results: List[Dict]):
        """Display comparison of different parameter combinations"""
        print("\n" + "="*80)
        print("📊 PARAMETER COMPARISON RESULTS")
        print("="*80)
        
        print(f"\n📋 Found {len(results)} different summaries:")
        print("-"*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n🔹 Summary {i}:")
            print(f"   Parameters: max_length={result['parameters'].get('max_length')}, "
                  f"min_length={result['parameters'].get('min_length')}, "
                  f"beams={result['parameters'].get('num_beams')}")
            print(f"   Length: {result['length']} words")
            print(f"   Compression Ratio: {result['compression_ratio']:.2%}")
            print(f"   Time: {result['time']:.2f}s")
            print(f"   Summary: {result['summary'][:150]}...")
            print("-"*60)
        
        # Best compression
        best_compression = min(results, key=lambda x: x['compression_ratio'])
        print(f"\n🏆 Best Compression: {best_compression['compression_ratio']:.2%}")
        print(f"   Parameters: max_length={best_compression['parameters'].get('max_length')}")
        
        # Fastest
        fastest = min(results, key=lambda x: x['time'])
        print(f"\n⚡ Fastest: {fastest['time']:.2f}s")
        print(f"   Parameters: max_length={fastest['parameters'].get('max_length')}")

### 5. Interactive Application


class SummarizationApp:
    """Interactive text summarization application"""
    
    def __init__(self):
        self.multi_model = MultiModelSummarizer()
        self.advanced = AdvancedSummarizer()
        self.current_model = 'pegasus_cnn'
        
        # Load default model
        self.multi_model.load_model('pegasus_cnn')
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "📝"*35)
        print("   TEXT SUMMARIZATION TOOL")
        print("   Powered by Transformers 🤗")
        print("📝"*35)
        print("\n📌 Summarize text using various models:")
        print("   - Pegasus (XSum, CNN)")
        print("   - BART")
        print("   - T5")
        print("\n" + "-"*70)
    
    def display_menu(self):
        """Display main menu"""
        print("\n📋 MAIN MENU")
        print("-"*50)
        print("1. 📊 Summarize Text")
        print("2. 🤖 Model Comparison")
        print("3. 🔬 Parameter Experimentation")
        print("4. 📈 View Statistics")
        print("5. 📜 View History")
        print("6. ⚙️ Change Model")
        print("7. 🎯 Custom Summarization")
        print("8. 💾 Export Results")
        print("9. 🧪 Test with Samples")
        print("10. ❌ Exit")
        print("-"*50)
    
    def summarize_text(self):
        """Summarize a single text"""
        print("\n📝 Enter text to summarize:")
        print("   (Type 'quit' to go back)")
        
        text = self._get_multiline_input()
        
        if not text:
            return
        
        print("\n🔄 Generating summary...")
        result = self.multi_model.summarize_with_model(
            self.current_model, 
            text,
            max_length=150,
            min_length=30,
            num_beams=4
        )
        
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
        else:
            self._display_summary(result, text)
    
    def _get_multiline_input(self) -> str:
        """Get multiline input from user"""
        lines = []
        print("\nEnter your text (press Enter twice to finish):")
        while True:
            line = input()
            if line == '' and lines:
                break
            if line != '':
                lines.append(line)
        return ' '.join(lines) if lines else ''
    
    def _display_summary(self, result: Dict, original_text: str):
        """Display the summary result"""
        print("\n" + "="*70)
        print("📊 SUMMARIZATION RESULT")
        print("="*70)
        
        print(f"\n📝 Original Text ({len(original_text.split())} words):")
        print("-"*50)
        print(original_text[:200] + "..." if len(original_text) > 200 else original_text)
        
        print(f"\n📋 Summary ({len(result['summary'].split())} words):")
        print("-"*50)
        print(result['summary'])
        
        print(f"\n📊 Metrics:")
        print(f"   Compression Ratio: {result.get('compression_ratio', 0):.2%}")
        print(f"   Generation Time: {result.get('generation_time', 0):.2f}s")
        print(f"   Model: {result.get('model', 'Unknown')}")
        print("="*70)
    
    def model_comparison(self):
        """Compare different models"""
        print("\n🤖 Model Comparison")
        print("Enter text to compare across models:")
        
        text = self._get_multiline_input()
        
        if not text:
            return
        
        if len(text.split()) < 30:
            print("⚠️ Text is too short for meaningful comparison.")
            print("Please enter at least 30 words.")
            return
        
        print("\n🔄 Running comparison across models...")
        print(f"📝 Input length: {len(text.split())} words")
        
        # Show available models
        available_models = ['pegasus_cnn', 'pegasus_xsum', 'bart']
        results = {}
        
        for model_key in available_models:
            result = self.multi_model.summarize_with_model(
                model_key, text,
                max_length=150,
                min_length=30,
                num_beams=4
            )
            if 'error' not in result:
                results[model_key] = {
                    'summary': result['summary'],
                    'length': len(result['summary'].split()),
                    'time': result.get('generation_time', 0),
                    'compression': result.get('compression_ratio', 0)
                }
        
        self.multi_model.display_comparison(results, text)
    
    def parameter_experimentation(self):
        """Run parameter experiments"""
        print("\n🔬 Parameter Experimentation")
        print("This will test different summary lengths and beam counts.")
        print("Enter text to summarize:")
        
        text = self._get_multiline_input()
        
        if not text:
            return
        
        # Experiment with different parameters
        param_sets = [
            {'max_length': 50, 'min_length': 10, 'num_beams': 2},
            {'max_length': 100, 'min_length': 20, 'num_beams': 4},
            {'max_length': 150, 'min_length': 30, 'num_beams': 6},
            {'max_length': 200, 'min_length': 40, 'num_beams': 8},
            {'max_length': 250, 'min_length': 50, 'num_beams': 10},
        ]
        
        results = []
        print("\n🔄 Running experiments...")
        
        for i, params in enumerate(param_sets, 1):
            print(f"\n🔹 Experiment {i}: max_len={params['max_length']}")
            result = self.multi_model.summarize_with_model(
                self.current_model, 
                text,
                **params
            )
            if 'error' not in result:
                results.append({
                    'parameters': params,
                    'summary': result['summary'],
                    'length': len(result['summary'].split()),
                    'time': result.get('generation_time', 0),
                    'compression': result.get('compression_ratio', 0)
                })
        
        self._display_experiment_results(results)
    
    def _display_experiment_results(self, results: List[Dict]):
        """Display experiment results"""
        print("\n" + "="*70)
        print("📊 EXPERIMENT RESULTS")
        print("="*70)
        
        for i, result in enumerate(results, 1):
            print(f"\n🔹 Result {i}:")
            print(f"   Parameters: max_length={result['parameters']['max_length']}, "
                  f"min_length={result['parameters']['min_length']}, "
                  f"beams={result['parameters']['num_beams']}")
            print(f"   Summary Length: {result['length']} words")
            print(f"   Compression: {result['compression']:.2%}")
            print(f"   Time: {result['time']:.2f}s")
            print(f"   Summary: {result['summary'][:150]}...")
            print("-"*60)
        
        # Best compression
        if results:
            best = min(results, key=lambda x: x['compression'])
            fastest = min(results, key=lambda x: x['time'])
            
            print(f"\n🏆 Best Compression: {best['compression']:.2%}")
            print(f"   Parameters: max_length={best['parameters']['max_length']}")
            
            print(f"\n⚡ Fastest: {fastest['time']:.2f}s")
            print(f"   Parameters: max_length={fastest['parameters']['max_length']}")
    
    def view_statistics(self):
        """View summarization statistics"""
        summarizer = self.multi_model.available_models[self.current_model]['model']
        stats = summarizer.get_statistics()
        
        print("\n" + "="*60)
        print("📊 SUMMARIZATION STATISTICS")
        print("="*60)
        
        if stats['total_summarized'] == 0:
            print("No data yet. Summarize some text first!")
            return
        
        print(f"\n📌 Model: {self.current_model}")
        print(f"\n📊 Total Summaries: {stats['total_summarized']}")
        print(f"   Average Input Length: {stats['avg_input_length']:.0f} characters")
        print(f"   Average Output Length: {stats['avg_output_length']:.0f} characters")
        print(f"   Average Compression Ratio: {stats['avg_compression_ratio']:.2%}")
        print(f"   Total Input Processed: {stats['total_chars_input']} characters")
        print(f"   Total Output Generated: {stats['total_chars_output']} characters")
        print("="*60)
    
    def view_history(self):
        """View summarization history"""
        summarizer = self.multi_model.available_models[self.current_model]['model']
        
        if not summarizer.history:
            print("\n📜 No history available.")
            return
        
        print("\n" + "="*60)
        print("📜 SUMMARIZATION HISTORY")
        print("="*60)
        
        # Show last 10 entries
        history = summarizer.history[-10:]
        
        for i, entry in enumerate(reversed(history), 1):
            print(f"\n{i}. 📅 {entry.get('timestamp', 'Unknown')}")
            print(f"   Input: {entry.get('text', '')[:100]}...")
            print(f"   Output: {entry.get('summary', '')[:100]}...")
            print(f"   Compression: {entry.get('compression_ratio', 0):.2%}")
            print("-"*50)
    
    def change_model(self):
        """Change the current model"""
        print("\n⚙️ Available Models:")
        models = self.multi_model.get_available_models()
        
        for i, model in enumerate(models, 1):
            status = "✅ Loaded" if model['loaded'] else "❌ Not loaded"
            print(f"{i}. {model['name']} - {status}")
            print(f"   {model['description']}")
        
        try:
            choice = int(input("\nSelect model (number): "))
            if 1 <= choice <= len(models):
                model_key = models[choice-1]['key']
                if self.multi_model.load_model(model_key):
                    self.current_model = model_key
                    print(f"✅ Model changed to: {model_key}")
                else:
                    print(f"❌ Failed to change model")
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def custom_summarization(self):
        """Custom summarization with advanced parameters"""
        print("\n🎯 Custom Summarization")
        print("Configure your own summarization parameters")
        
        text = self._get_multiline_input()
        if not text:
            return
        
        # Get parameters
        print("\nConfigure parameters (press Enter for default values):")
        
        try:
            max_len = input("Max length (default 150): ").strip()
            max_len = int(max_len) if max_len else 150
            
            min_len = input("Min length (default 30): ").strip()
            min_len = int(min_len) if min_len else 30
            
            beams = input("Number of beams (default 4): ").strip()
            beams = int(beams) if beams else 4
            
            temp = input("Temperature (default 0.7): ").strip()
            temp = float(temp) if temp else 0.7
            
            sample = input("Use sampling? (y/n, default n): ").strip().lower()
            sample = sample == 'y'
            
            penalty = input("Length penalty (default 2.0): ").strip()
            penalty = float(penalty) if penalty else 2.0
            
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            return
        
        print("\n🔄 Generating custom summary...")
        result = self.multi_model.summarize_with_model(
            self.current_model,
            text,
            max_length=max_len,
            min_length=min_len,
            num_beams=beams,
            do_sample=sample,
            temperature=temp,
            length_penalty=penalty
        )
        
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
        else:
            self._display_summary(result, text)
    
    def export_results(self):
        """Export summarization results"""
        summarizer = self.multi_model.available_models[self.current_model]['model']
        
        if not summarizer.history:
            print("\n📁 No data to export.")
            return
        
        import json
        filename = f"summarization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'model': self.current_model,
                'statistics': summarizer.get_statistics(),
                'history': summarizer.history
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Results exported to '{filename}'")
            print(f"📁 Contains {len(summarizer.history)} summaries")
            
        except Exception as e:
            print(f"❌ Error exporting results: {e}")
    
    def test_samples(self):
        """Test with sample texts"""
        sample_texts = [
            """Artificial intelligence (AI) is transforming the world in unprecedented ways. 
            From healthcare to transportation, AI systems are being deployed to solve complex problems 
            and improve efficiency. However, the rapid advancement of AI also raises important questions 
            about ethics, privacy, and the future of work. As AI continues to evolve, it is crucial that 
            we develop frameworks to ensure its responsible development and deployment.""",
            
            """Climate change poses one of the greatest challenges of our time. Rising global temperatures, 
            extreme weather events, and sea-level rise are already affecting communities worldwide. 
            Scientists warn that without immediate action, the consequences will become increasingly severe. 
            Governments, businesses, and individuals must work together to reduce greenhouse gas emissions 
            and transition to sustainable energy sources.""",
            
            """The COVID-19 pandemic has fundamentally changed how we live, work, and interact with each other. 
            Remote work has become the norm for many, virtual learning has transformed education, 
            and digital services have become essential. While the pandemic has accelerated technological 
            adoption, it has also highlighted existing inequalities and the importance of public health systems."""
        ]
        
        print("\n🧪 TESTING WITH SAMPLE TEXTS")
        print("="*60)
        
        for i, text in enumerate(sample_texts, 1):
            print(f"\n📝 Sample {i} ({len(text.split())} words):")
            print("-"*40)
            print(text[:150] + "..." if len(text) > 150 else text)
            
            print("\n🔄 Generating summary...")
            result = self.multi_model.summarize_with_model(
                self.current_model,
                text,
                max_length=100,
                min_length=20,
                num_beams=4
            )
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n📋 Summary ({len(result['summary'].split())} words):")
                print(result['summary'])
                print(f"\n📊 Compression Ratio: {result.get('compression_ratio', 0):.2%}")
            
            print("-"*60)
    
    def run(self):
        """Main application loop"""
        self.display_welcome()
        
        while True:
            self.display_menu()
            choice = input("\nSelect option (1-10): ").strip()
            
            if choice == '1':
                self.summarize_text()
            elif choice == '2':
                self.model_comparison()
            elif choice == '3':
                self.parameter_experimentation()
            elif choice == '4':
                self.view_statistics()
            elif choice == '5':
                self.view_history()
            elif choice == '6':
                self.change_model()
            elif choice == '7':
                self.custom_summarization()
            elif choice == '8':
                self.export_results()
            elif choice == '9':
                self.test_samples()
            elif choice == '10':
                print("\n👋 Thanks for using the Summarization Tool!")
                print("📝 Keep summarizing and learning!")
                break
            else:
                print("❌ Invalid option. Please choose 1-10.")

### 6. Unit Tests

import unittest
from unittest.mock import patch, MagicMock

class TestTextSummarizer(unittest.TestCase):
    def setUp(self):
        self.summarizer = TextSummarizer('google/pegasus-cnn_dailymail')
    
    def test_summarize(self):
        """Test basic summarization"""
        text = "This is a test text that is long enough to be summarized effectively. " * 5
        result = self.summarizer.summarize(text)
        self.assertIn('summary', result)
        self.assertNotIn('error', result)
    
    def test_empty_text(self):
        """Test empty text handling"""
        result = self.summarizer.summarize("")
        self.assertIn('error', result)
    
    def test_summary_length(self):
        """Test summary length constraints"""
        text = "This is a test. " * 20
        result = self.summarizer.summarize(text, max_length=20)
        if 'error' not in result:
            self.assertLessEqual(len(result['summary'].split()), 25)
    
    def test_statistics(self):
        """Test statistics tracking"""
        self.summarizer.summarize("Test text")
        stats = self.summarizer.get_statistics()
        self.assertEqual(stats['total_summarized'], 1)
    
    def test_compression_ratio(self):
        """Test compression ratio calculation"""
        text = "This is a test text." * 10
        result = self.summarizer.summarize(text)
        if 'error' not in result:
            self.assertGreaterEqual(result.get('compression_ratio', 0), 0)

class TestMultiModelSummarizer(unittest.TestCase):
    def setUp(self):
        self.multi = MultiModelSummarizer()
    
    def test_available_models(self):
        """Test available models list"""
        models = self.multi.get_available_models()
        self.assertGreater(len(models), 0)
    
    def test_load_model(self):
        """Test model loading"""
        result = self.multi.load_model('pegasus_cnn')
        self.assertTrue(result)
    
    def test_invalid_model(self):
        """Test invalid model handling"""
        result = self.multi.load_model('invalid_model')
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()

#pip install transformers torch sentencepiece
# For additional features
#pip install nltk rouge-score