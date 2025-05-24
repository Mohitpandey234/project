import os
from groq import Groq

class LLMService:
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = Groq(
            api_key=api_key
        )

    def generate_response(self, prompt):
        try:
            # Create a more focused system prompt
            system_prompt = """You are a helpful store management assistant. Your primary tasks are:
1. Help with inventory management (adding, updating, deleting items)
2. Assist with billing and order processing
3. Answer questions about store operations

Please keep responses concise and focused on the task at hand. If you're unsure about a command, explain the correct format.

Available commands:
- add [item] [price] - Add new item
- update price [item] [price] - Update item price
- update name [old] [new] - Rename item
- delete [item] - Remove item
- [quantity] [item] - Add to bill
- put [X]% discount on item [Y] - Apply discount
- change quantity of item [X] from [Y] to [Z] - Update quantity
- print - Finalize and save bill"""

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama2-70b",  # Using the correct model name
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=200    # Limit response length
            )
            
            response = chat_completion.choices[0].message.content
            
            # Clean up and format the response
            response = response.strip()
            if not response:
                return "I apologize, but I couldn't generate a proper response. Please try rephrasing your request."
                
            return response

        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower():
                return "Error: API key validation failed. Please check the API key configuration."
            elif "connection" in error_msg.lower():
                return "Error: Could not connect to the LLM service. Please check your internet connection."
            else:
                return f"An error occurred: {error_msg}. Please try again or contact support."

# Initialize the service
llm_service = LLMService()

# Export the generate_response function
def generate_response(prompt):
    return llm_service.generate_response(prompt) 