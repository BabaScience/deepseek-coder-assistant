from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

class CodeAssistant:
    def __init__(self, model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device_map="auto"
        )

    def generate_code(self, prompt, max_length=500, temperature=0.9):
        messages = [
            {"role": "user", "content": prompt}
        ]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(self.model.device)
        
        outputs = self.model.generate(
            inputs,
            max_length=max_length,
            temperature=temperature,
            do_sample=True,
            top_p=0.95,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        return self.tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)

if __name__ == "__main__":
    assistant = CodeAssistant()
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            response = assistant.generate_code(user_input)
            print("\nAssistant:", response)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {str(e)}")