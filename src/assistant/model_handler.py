import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from ..utils.logger import logger

class ModelHandler:
    def __init__(self, model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
        logger.info(f"Initializing model handler with model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )

    def generate(self, prompt, max_length=2048, temperature=0.7):
        """Generate code based on the given prompt."""
        try:
            messages = [{"role": "user", "content": prompt}]
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
            
            generated_text = self.tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
            
            # Remove code block wrapping
            if generated_text.startswith("```"):
                # Find the first newline after the opening ```
                first_newline = generated_text.find('\n')
                if first_newline != -1:
                    # Remove the opening ```
                    code = generated_text[first_newline + 1:]
                    # Remove the closing ```
                    if "```" in code:
                        code = code[:code.rindex("```")]
                    return code.strip()
            
            return generated_text.strip()
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise

