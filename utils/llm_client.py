"""
Multi-Provider LLM Client - Supports Mistral API, Gemini API, and Ollama
"""
import json
import os
import requests
from typing import Optional, Dict, Any
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    def __init__(self):
        # Determine provider from environment - prioritize Mistral if key is available
        self.provider = os.getenv("LLM_PROVIDER", "auto").lower()  # mistral, gemini, ollama, or auto
        
        # API Keys
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        
        # Model selection per provider
        self.mistral_model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")  # or mistral-medium-latest
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # or gemini-1.5-pro
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Auto-select provider based on available API keys (prioritize Mistral)
        if self.provider == "auto":
            if self.mistral_api_key:
                self.provider = "mistral"
                logger.info("Auto-selected Mistral API (API key found)")
            elif self.gemini_api_key:
                self.provider = "gemini"
                logger.info("Auto-selected Gemini API (API key found)")
            else:
                self.provider = "ollama"
                logger.info("Auto-selected Ollama (no API keys found, using local)")
        
        # If explicitly set to mistral but no key, try to use it anyway (might be set elsewhere)
        if self.provider == "mistral" and not self.mistral_api_key:
            logger.warning("Mistral API key not found in environment, but provider is set to mistral")
            logger.warning("Please ensure MISTRAL_API_KEY is set in .env file")
            # Don't fall back - let it fail explicitly so user knows to set the key
        elif self.provider == "gemini" and not self.gemini_api_key:
            logger.warning("Gemini API key not found, falling back to Ollama")
            self.provider = "ollama"
        
        logger.info(f"LLM Provider: {self.provider.upper()}")
        if self.provider == "mistral":
            logger.info(f"Using Mistral model: {self.mistral_model}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        json_mode: bool = False,
        timeout: Optional[int] = None  # Auto-adjusts based on provider
    ) -> str:
        """
        Generate text using the configured provider
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Creativity level (0-1)
            max_tokens: Maximum response length
            json_mode: Force JSON output
            timeout: Request timeout in seconds (None = auto-adjust based on provider)
            
        Returns:
            Generated text
        """
        # Auto-adjust timeout based on provider if not specified
        if timeout is None:
            if self.provider in ["mistral", "gemini"]:
                timeout = 60  # APIs are fast
            else:
                timeout = 300  # Ollama is slower
        
        if self.provider == "mistral":
            return self._generate_mistral(prompt, system_prompt, temperature, max_tokens, json_mode, timeout)
        elif self.provider == "gemini":
            return self._generate_gemini(prompt, system_prompt, temperature, max_tokens, json_mode, timeout)
        else:
            return self._generate_ollama(prompt, system_prompt, temperature, max_tokens, json_mode, timeout)
    
    def _generate_mistral(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        timeout: int
    ) -> str:
        """Generate using Mistral API"""
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.mistral_api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.mistral_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
                logger.success(f"Generated {len(generated_text)} characters via Mistral API")
                return generated_text
            else:
                logger.error("Unexpected Mistral API response structure")
                raise ValueError("Invalid response from Mistral API")
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_json = e.response.json()
                error_detail = error_json.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            logger.error(f"Mistral API HTTP error: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise
    
    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        timeout: int
    ) -> str:
        """Generate using Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"
        params = {"key": self.gemini_api_key}
        
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        if json_mode:
            full_prompt += "\n\nRespond ONLY with valid JSON. No explanation text."
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        # Gemini 1.5+ supports JSON schema for structured output
        if json_mode and "1.5" in self.gemini_model:
            payload["generationConfig"]["response_mime_type"] = "application/json"
        
        try:
            response = requests.post(url, json=payload, params=params, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            
            # Handle Gemini response structure
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    generated_text = candidate["content"]["parts"][0]["text"]
                    logger.success(f"Generated {len(generated_text)} characters via Gemini API")
                    return generated_text
            
            # Fallback if structure is different
            logger.warning("Unexpected Gemini API response structure")
            return str(result)
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_json = e.response.json()
                error_detail = error_json.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            logger.error(f"Gemini API HTTP error: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        timeout: int
    ) -> str:
        """Generate using Ollama (fallback)"""
        api_url = f"{self.ollama_base_url}/api/generate"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        if json_mode:
            full_prompt += "\n\nRespond ONLY with valid JSON. No explanation text."
        
        payload = {
            "model": self.ollama_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending request to Ollama (model={self.ollama_model}, attempt {attempt+1}/{max_retries})")
                response = requests.post(api_url, json=payload, timeout=timeout)
                response.raise_for_status()
                result = response.json()
                generated_text = result.get("response", "")
                logger.success(f"Generated {len(generated_text)} characters via Ollama")
                return generated_text
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout on attempt {attempt+1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                timeout = timeout + 120
            except Exception as e:
                logger.error(f"Ollama error: {e}")
                raise
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        timeout: Optional[int] = None  # Auto-adjusts based on provider
    ) -> Dict[str, Any]:
        """
        Generate JSON output with automatic parsing
        
        Returns:
            Parsed JSON dictionary
        """
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            json_mode=True,
            timeout=timeout
        )
        
        # Extract JSON from response (handle markdown code blocks)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Find JSON object boundaries (for incomplete responses)
        start_curly = response.find('{')
        start_bracket = response.find('[')
        
        if start_curly == -1 and start_bracket == -1:
            # No JSON found at all - return empty dict
            logger.warning("No JSON structure found in response, returning empty dict")
            return {}
        
        if start_curly != -1 and (start_bracket == -1 or start_curly < start_bracket):
            last_brace = response.rfind('}')
            if last_brace != -1 and last_brace > start_curly:
                response = response[start_curly:last_brace+1]
            else:
                response = response[start_curly:]
                if not response.endswith('}'):
                    open_count = response.count('{') - response.count('}')
                    response = response + '}' * open_count
        elif start_bracket != -1:
            last_bracket = response.rfind(']')
            if last_bracket != -1 and last_bracket > start_bracket:
                response = response[start_bracket:last_bracket+1]
            else:
                response = response[start_bracket:]
                if not response.endswith(']'):
                    open_count = response.count('[') - response.count(']')
                    response = response + ']' * open_count
        
        # Fix common JSON issues
        response = self._fix_json_string(response)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON on first attempt: {e}")
            logger.debug(f"Raw response (first 500 chars): {response[:500]}...")
            
            try:
                cleaned = self._aggressive_json_clean(response)
                result = json.loads(cleaned)
                # Ensure we return a dict, not a string or other type
                if not isinstance(result, dict):
                    logger.warning(f"JSON parsed but result is not a dict (type: {type(result)}), using fallback")
                    return self._extract_partial_json(response)
                return result
            except Exception as clean_e:
                logger.error(f"Even aggressive cleaning failed: {clean_e}")
                try:
                    partial_result = self._extract_partial_json(response)
                    # Ensure partial result is a dict
                    if not isinstance(partial_result, dict):
                        logger.warning(f"Partial extraction returned non-dict (type: {type(partial_result)}), returning empty dict")
                        return {}
                    return partial_result
                except Exception as extract_e:
                    logger.error(f"Partial extraction also failed: {extract_e}")
                    raise ValueError(f"Invalid JSON response: {e}")
    
    def _fix_json_string(self, text: str) -> str:
        """Fix common JSON formatting issues"""
        import re
        
        def remove_control_chars(s):
            return ''.join(char for char in s if ord(char) >= 32 or char in '\t\n\r')
        
        text = remove_control_chars(text)
        
        def fix_escapes(match):
            char_after = match.group(1)
            if char_after in ['"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u']:
                return match.group(0)
            else:
                return '\\\\' + char_after
        
        text = re.sub(r'\\(.)', fix_escapes, text)
        
        # Fix missing commas between fields
        text = re.sub(r'("[^"]*")\s*(")', r'\1, \2', text)
        # Fix trailing commas
        text = re.sub(r',\s*([\]}])', r'\1', text)
        
        return text
    
    def _aggressive_json_clean(self, text: str) -> str:
        """Aggressively clean JSON string as last resort"""
        import re
        
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        text = text.replace('\\', '\\\\')
        text = text.replace('\\\\n', '\\n')
        text = text.replace('\\\\r', '\\r')
        text = text.replace('\\\\t', '\\t')
        text = text.replace('\\\\"', '\\"')
        text = text.replace('\\\\\\\\', '\\\\')
        
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')
        
        return text
    
    def _extract_partial_json(self, text: str) -> Dict[str, Any]:
        """Extract partial JSON from incomplete responses"""
        import re
        
        result = {}
        
        pattern = r'"([^"]+)"\s*:\s*"([^"]*)"'
        matches = re.findall(pattern, text)
        for key, value in matches:
            result[key] = value
        
        pattern2 = r'"([^"]+)"\s*:\s*([^,}\]]+)'
        matches2 = re.findall(pattern2, text)
        for key, value in matches2:
            value = value.strip().rstrip(',}')
            if value.lower() == 'true':
                result[key] = True
            elif value.lower() == 'false':
                result[key] = False
            elif value.isdigit():
                result[key] = int(value)
            elif re.match(r'^\d+\.\d+$', value):
                result[key] = float(value)
            else:
                result[key] = value
        
        if result:
            logger.warning("Extracted partial JSON from incomplete response")
            return result
        
        logger.warning("Could not extract any JSON, returning empty dict")
        return {}
    
    def test_connection(self) -> bool:
        """Test connection to configured provider"""
        if self.provider == "mistral":
            try:
                url = "https://api.mistral.ai/v1/models"
                headers = {"Authorization": f"Bearer {self.mistral_api_key}"}
                response = requests.get(url, headers=headers, timeout=5)
                response.raise_for_status()
                logger.success("Mistral API connection successful")
                return True
            except Exception as e:
                logger.error(f"Cannot connect to Mistral API: {e}")
                return False
        elif self.provider == "gemini":
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}?key={self.gemini_api_key}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                logger.success("Gemini API connection successful")
                return True
            except Exception as e:
                logger.error(f"Cannot connect to Gemini API: {e}")
                return False
        else:
            try:
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                response.raise_for_status()
                logger.success("Ollama connection successful")
                return True
            except Exception as e:
                logger.error(f"Cannot connect to Ollama: {e}")
                return False


# Global client instance
llm_client = LLMClient()
