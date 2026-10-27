"""
Model Conversion Using Pre-built llama.cpp Binaries
Download pre-compiled tools instead of building from source

Requirements:
1. llama_1b_merged_full folder
2. Internet connection
3. Run: python prebuilt_binary_conversion.py
"""

import os
import sys
import subprocess
import zipfile
import urllib.request
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def download_prebuilt_binaries():
    """Download pre-built llama.cpp binaries for Windows"""
    print_header("Step 1: Downloading Pre-built Tools")
    
    # Check if already downloaded
    if os.path.exists("llama-cpp-windows"):
        print("鉁?Pre-built binaries already exist")
        return True
    
    print("馃摜 Downloading pre-built llama.cpp for Windows...")
    print("   This is about 50-100 MB")
    
    # URL for pre-built Windows binaries (this is an example, adjust if needed)
    # We'll use the GitHub releases
    binary_url = "https://github.com/ggerganov/llama.cpp/releases/latest/download/llama-b3561-bin-win-avx2-x64.zip"
    
    try:
        print(f"   Downloading from: {binary_url}")
        print("   Please wait...")
        
        urllib.request.urlretrieve(binary_url, "llama-cpp-binaries.zip")
        
        print("馃摝 Extracting...")
        with zipfile.ZipFile("llama-cpp-binaries.zip", 'r') as zip_ref:
            zip_ref.extractall("llama-cpp-windows")
        
        print("鉁?Downloaded and extracted!")
        
        # Clean up zip
        os.remove("llama-cpp-binaries.zip")
        
        return True
        
    except Exception as e:
        print(f"鉂?Download failed: {e}")
        print("\n馃挕 Manual download:")
        print("   1. Visit: https://github.com/ggerganov/llama.cpp/releases")
        print("   2. Download the Windows binary (llama-*-bin-win-*.zip)")
        print("   3. Extract to folder: llama-cpp-windows")
        return False

def convert_with_python_only():
    """Try conversion using pure Python approach"""
    print_header("Alternative: Python-Only Conversion")
    
    print("Let's try a simpler conversion method...")
    print("Using transformers library directly")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        print("\n馃搨 Loading model...")
        model = AutoModelForCausalLM.from_pretrained("llama_1b_merged_full")
        tokenizer = AutoTokenizer.from_pretrained("llama_1b_merged_full")
        
        print("鉁?Model loaded successfully!")
        
        # Save in a format Ollama might accept
        print("\n馃捑 Saving in compatible format...")
        
        output_dir = "llama_1b_for_ollama"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save with safetensors (preferred by Ollama)
        model.save_pretrained(output_dir, safe_serialization=True)
        tokenizer.save_pretrained(output_dir)
        
        print(f"鉁?Saved to: {output_dir}")
        print("\nNow let's try importing this to Ollama...")
        
        return output_dir
        
    except Exception as e:
        print(f"鉂?Conversion failed: {e}")
        return None

def create_modelfile(model_path):
    """Create Modelfile for Ollama"""
    print_header("Step 2: Creating Modelfile")
    
    model_path = os.path.abspath(model_path).replace("\\", "/")
    
    modelfile_content = f"""# Fine-tuned Llama Model
FROM {model_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 256

SYSTEM \"\"\"You are a helpful financial literacy assistant for Malaysian youth. You provide clear, accurate, and practical financial advice based on Malaysian context, including EPF (KWSP) information and local financial practices.\"\"\"
"""
    
    with open("Modelfile_Clean", 'w', encoding='utf-8') as f:
        f.write(modelfile_content)
    
    print("鉁?Modelfile created with UTF-8 encoding")
    print(f"   Model path: {model_path}")
    
    return True

def import_to_ollama(model_name="my-finetuned"):
    """Import to Ollama"""
    print_header("Step 3: Importing to Ollama")
    
    print(f"馃摝 Importing as: {model_name}")
    
    # Check if exists
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if model_name in result.stdout:
            print(f"鈿狅笍  Model '{model_name}' exists")
            response = input("   Replace? (y/n): ")
            if response.lower() == 'y':
                subprocess.run(['ollama', 'rm', model_name])
            else:
                return True
    except:
        pass
    
    # Import with explicit encoding
    cmd = ['ollama', 'create', model_name, '-f', 'Modelfile_Clean']
    
    try:
        # Set encoding environment variable
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            env=env
        )
        print(result.stdout)
        print(f"\n鉁?Import successful!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"鉂?Import failed")
        try:
            print(f"Error: {e.stderr}")
        except:
            print("Error output couldn't be decoded")
        return False

def try_upload_to_huggingface():
    """Suggest uploading to HuggingFace as alternative"""
    print_header("Alternative Approach")
    
    print("Since direct conversion is challenging, here are alternatives:")
    print("\n1锔忊儯  Upload to HuggingFace Hub (Free, Public)")
    print("   - Create account at huggingface.co")
    print("   - Upload your model")
    print("   - Use: ollama pull hf.co/yourusername/model-name")
    
    print("\n2锔忊儯  Use Google Colab for Conversion")
    print("   - Free GPU environment")
    print("   - Can build llama.cpp there")
    print("   - Download GGUF file")
    
    print("\n3锔忊儯  Ask a Friend with Mac/Linux")
    print("   - Conversion is easier on Unix systems")
    print("   - They can send you the GGUF file")
    
    print("\n4锔忊儯  Use Online Converter Services")
    print("   - Some services convert models online")
    print("   - Example: huggingface.co/spaces")

def main():
    """Main process"""
    print_header("馃殌 Pre-built Binary Conversion Method")
    
    print("This approach:")
    print("  鉁?Uses pre-built tools (no compilation)")
    print("  鉁?Handles encoding issues")
    print("  鉁?Multiple fallback methods")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Check if model folder exists
    if not os.path.exists("llama_1b_merged_full"):
        print("鉂?Model folder not found!")
        return
    
    print("\n" + "="*70)
    print("  Attempting Method 1: Python-Only Conversion")
    print("="*70)
    
    # Try Python-only conversion first
    converted_model = convert_with_python_only()
    
    if converted_model:
        # Create Modelfile
        if create_modelfile(converted_model):
            # Get model name
            model_name = input("\nEnter model name (default: my-finetuned): ").strip()
            if not model_name:
                model_name = "my-finetuned"
            
            # Try import
            if import_to_ollama(model_name):
                print_header("馃帀 SUCCESS!")
                print(f"鉁?Model imported: {model_name}")
                print(f"\nTest it: ollama run {model_name}")
                return
    
    # If that failed, show alternatives
    print("\n" + "="*70)
    print("  Method 1 didn't work. Here are alternatives:")
    print("="*70)
    
    try_upload_to_huggingface()
    
    print("\n馃挕 Recommended: Try the Google Colab method")
    print("   It's free and will definitely work!")
    print("\n   Would you like instructions for Google Colab conversion?")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n鈿狅笍  Interrupted")
    except Exception as e:
        print(f"\n\n鉂?Error: {e}")
        import traceback
        traceback.print_exc()