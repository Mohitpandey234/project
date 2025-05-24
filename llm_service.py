from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LLMService:
    def __init__(self):
        # Using BLOOMZ-560M, a lightweight multilingual model
        self.model_name = "bigscience/bloomz-560m"
        print("Loading model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            device_map="auto"
        )
        print("Model loaded successfully!")

    def generate_response(self, prompt, max_length=100):
        try:
            # Prepare the input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate response
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode and return the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response[len(prompt):].strip()
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error processing your request."

# Initialize the service (will be imported by market.py)
llm_service = LLMService() 