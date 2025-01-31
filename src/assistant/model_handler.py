import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from ..utils.logger import logger
from ..utils.exceptions import CodeAssistantError
import time

class ModelHandler:
    def __init__(self, model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
        logger.info(f"Initializing model handler with model: {model_name}")
        
        try:
            device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,  # Use float16 for better memory efficiency
                device_map={"": device},
                trust_remote_code=True
            )
            logger.info(f"Model loaded on device: {device}")
        except Exception as e:
            logger.error(f"Failed to initialize model with GPU, falling back to CPU: {str(e)}")
            # Fallback to CPU if GPU initialization fails
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True
            )



    def generate(self, prompt, max_new_tokens=4096, temperature=0.7):
        try:
            logger.info("Starting code generation...")
            logger.info("Tokenizing input...")
            messages = [{"role": "user", "content": prompt}]
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt"
            ).to(self.model.device)
            
            logger.info(f"Input tokens: {len(inputs[0])}")
            logger.info("Generating response...")
            
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info("Decoding response...")
            # return self.tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
        
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
            logger.error(f"Generation failed: {str(e)}")
            raise


class LoggingCallback:
    def __init__(self):
        self.start_time = time.time()
        
    def on_step(self, args, state, control):
        elapsed = time.time() - self.start_time
        logger.info(f"Generated {state.current_length} tokens in {elapsed:.2f}s")
        return control
