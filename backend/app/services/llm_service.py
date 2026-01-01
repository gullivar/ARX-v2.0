import requests
import logging
import json
import socket
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.internal_host = "192.168.8.190"
        self.external_host = "106.254.248.154"
        self.port = 17311
        self.model = "llama3:latest"
        self.base_url = None # Lazy init to avoid startup blocking

    def _check_host(self, host: str, timeout: float = 2.0) -> bool:
        try:
            url = f"http://{host}:{self.port}/api/version"
            requests.get(url, timeout=timeout)
            return True
        except:
            return False

    def refresh_connection_status(self):
        """
        Periodic check to optimize connection path.
        - Prioritizes Internal (Direct) IP if available for speed.
        - Fallbacks to External (Port Forwarding) if Internal is unreachable.
        """
        logger.info("Optimizing LLM Connection Path...")
        
        # 1. Try Internal First
        if self._check_host(self.internal_host, timeout=1.0):
            new_url = f"http://{self.internal_host}:{self.port}"
            if self.base_url != new_url:
                logger.info(f"✅ Switched LLM Connection to INTERNAL (Direct): {new_url}")
            self.base_url = new_url
            return

        # 2. Try External
        if self._check_host(self.external_host, timeout=3.0):
            new_url = f"http://{self.external_host}:{self.port}"
            if self.base_url != new_url:
                logger.warning(f"⚠️ Switched LLM Connection to EXTERNAL (Relay): {new_url}")
            self.base_url = new_url
            return

        logger.error("❌ Both Internal and External LLM connections failed.")

    def _determine_base_url(self) -> str:
        """
        Check connectivity to internal IP first, then fallback to external IP.
        """
        urls_to_try = [
            f"http://{self.internal_host}:{self.port}",
            f"http://{self.external_host}:{self.port}"
        ]

        for url in urls_to_try:
            try:
                # Increased timeout to 3s to allow for latency
                requests.get(f"{url}/api/version", timeout=3.0)
                logger.info(f"LLM Service connected via: {url}")
                return url
            except Exception as e:
                logger.warning(f"LLM Connection failed for {url}: {e}")
                continue
        
        logger.error("Could not connect to LLM Service on any known address. Defaulting to External for safety.")
        return f"http://{self.external_host}:{self.port}" # Default to External if both fail (better chance when remote)

    def get_base_url(self):
        if not self.base_url:
            self.base_url = self._determine_base_url()
        return self.base_url

    def check_health(self) -> bool:
        url = self.get_base_url()
        try:
            requests.get(f"{url}/api/version", timeout=3.0)
            return True
        except:
            # Force re-determination
            self.base_url = self._determine_base_url()
            return True # Assume new URL might work, next call will verify
            
    def analyze_content(self, title: str, content: str, category_definitions: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Send content to LLM for classification.
        category_definitions: Dict where key=CategoryName, value=Description
        """
        # Retry logic wrapper
        for attempt in range(2):
            url = self.get_base_url()
            
            # Construct Category Prompt Part
            category_prompt = ""
            if category_definitions:
                category_prompt = "Select the single most appropriate category from the list below based on the definitions:\n"
                for cat, desc in category_definitions.items():
                    desc_text = f": {desc}" if desc else ""
                    category_prompt += f"- {cat}{desc_text}\n"
            else:
                # Fallback default if not provided
                category_prompt = "Determine the Main Category (e.g., Shopping, Banking, Gambling, Phishing, Malware, News, Tech, Uncategorized)."

            prompt = f"""
            Analyze the following webpage content and classify it for a threat intelligence database.
            
            Title: {title}
            Content Snippet: {content[:4000]}
            
            Task:
            1. {category_prompt}
            2. Determine if it is malicious (True/False).
            3. Provide a confidence score (0.0 to 1.0).
            4. Provide a 1-sentence summary.
            
            Output valid JSON only:
            {{
                "category_main": "CategoryName",
                "is_malicious": false,
                "confidence_score": 0.9,
                "summary": "This site is..."
            }}
            """
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            
            try:
                # Timeout 30s for analysis (Fail Fast)
                response = requests.post(f"{url}/api/generate", json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("response", "{}")
                    data = json.loads(llm_response)
                    data["llm_model_used"] = self.model
                    return data
                else:
                    logger.error(f"LLM API Error: {response.text}")
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"LLM Request Failed (Attempt {attempt+1}): {e}")
                # Force refresh connection for next attempt
                self.base_url = None
                self.refresh_connection_status()
                continue
            except Exception as e:
                logger.error(f"LLM Analysis Failed: {e}")
                return None
        return None

    def simple_chat(self, prompt: str) -> str:
        """
        Generic chat completion.
        """
        for attempt in range(2):
            url = self.get_base_url()
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            try:
                # 60s timeout for chat
                response = requests.post(f"{url}/api/generate", json=payload, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "No response from LLM.")
                return f"LLM Error: {response.text}"
            except requests.exceptions.RequestException as e:
                logger.warning(f"LLM Chat Failed (Attempt {attempt+1}): {e}")
                self.base_url = None
                self.refresh_connection_status()
                continue
            except Exception as e:
                logger.error(f"LLM Chat Failed: {e}")
                return f"System Error: {str(e)}"
        
    async def get_async_client(self):
        """
        Lazy init of persistent async client
        """
        import httpx
        if not hasattr(self, "_async_client") or self._async_client is None:
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
            timeout = httpx.Timeout(120.0, connect=10.0)
            self._async_client = httpx.AsyncClient(limits=limits, timeout=timeout, verify=False)
        return self._async_client

    async def analyze_content_async(self, title: str, content: str, category_definitions: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Async version using persistent HTTPX client
        """
        client = await self.get_async_client()
        
        for attempt in range(2):
            url = self.get_base_url()
            
            # Construct Category Prompt Part
            category_prompt = ""
            if category_definitions:
                category_prompt = "Select the single most appropriate category from the list below based on the definitions:\n"
                for cat, desc in category_definitions.items():
                    desc_text = f": {desc}" if desc else ""
                    category_prompt += f"- {cat}{desc_text}\n"
            else:
                category_prompt = "Determine the Main Category (e.g., Shopping, Banking, Gambling, Phishing, Malware, News, Tech, Uncategorized)."

            prompt = f"""
            Analyze the following webpage content and classify it for a threat intelligence database.
            
            Title: {title}
            Content Snippet: {content[:4000]}
            
            Task:
            1. {category_prompt}
            2. Determine if it is malicious (True/False).
            3. Provide a confidence score (0.0 to 1.0).
            4. Provide a 1-sentence summary.
            
            Output valid JSON only:
            {{
                "category_main": "CategoryName",
                "is_malicious": false,
                "confidence_score": 0.9,
                "summary": "This site is..."
            }}
            """
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            
            try:
                response = await client.post(f"{url}/api/generate", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("response", "{}")
                    data = json.loads(llm_response)
                    data["llm_model_used"] = self.model
                    return data
                else:
                    logger.error(f"LLM API Error (Async): {response.text}")
                    return None
            except Exception as e:
                logger.warning(f"LLM Async Request Failed (Attempt {attempt+1}): {e}")
                self.base_url = None
                self.refresh_connection_status()
                continue
        return None

    # Helper to close client on shutdown
    async def close(self):
        if hasattr(self, "_async_client") and self._async_client:
            await self._async_client.aclose()

llm_service = LLMService()
