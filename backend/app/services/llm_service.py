
print("DEBUG: LOADED NEW LLM_SERVICE MODULE WITH EXTERNAL HOST FIX V3")
import requests
import logging
import json
import os
import random
import asyncio
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.internal_host = "192.168.8.190"
        self.external_host = "106.254.248.154"
        self.port = 17311
        self.local_model = "llama3:latest"
        self.base_url = None 
        self.use_public_llm = False
        print(f"DEBUG: LLMService Initialized. External Host: {self.external_host}")

    def refresh_connection_status(self):
        print(f"DEBUG: Checking connectivity to {self.external_host}...")
        if self._check_host(self.external_host):
            self.base_url = f"http://{self.external_host}:{self.port}"
            print(f"✅ Connected to External GPU LLM: {self.base_url}")
        elif self._check_host(self.internal_host):
            self.base_url = f"http://{self.internal_host}:{self.port}"
            print(f"✅ Connected to Internal GPU LLM: {self.base_url}")
        else:
            print("❌ Failed to connect to any GPU LLM Host.")
            self.base_url = None
            
    def _check_host(self, host: str, timeout: float = 10.0) -> bool:
        try:
            url = f"http://{host}:{self.port}/api/version"
            resp = requests.get(url, timeout=timeout)
            return resp.status_code == 200
        except Exception as e:
            print(f"DEBUG: Connection Error to {host}: {e}")
            return False

    def get_base_url(self):
        if self.base_url: return self.base_url
        self.refresh_connection_status()
        return self.base_url

    async def analyze_content_async(self, title: str, content: str, category_definitions: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return await self._analyze_with_local(title, content, category_definitions)

    async def analyze_batch_async(self, items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        if not items: return []
        
        prompt = "Analyze the following websites and return a JSON list.\n"
        prompt += "Output format: [{'fqdn': '...', 'category_main': '...', 'is_malicious': bool, 'summary': '...'}, ...]\n\n"
        
        for item in items:
            prompt += f"--- Site: {item['fqdn']} ---\n"
            prompt += f"Title: {item['title'][:100]}\n"
            prompt += f"Content: {item['content'][:300]}\n\n" # Reduced context even more
            
        prompt += "RETURN ONLY JSON LIST. NO EXTRA TEXT."
        
        try:
            import httpx
            url = self.get_base_url()
            if not url: return []

            print(f"Sending Batch Request (Size {len(items)}) to {url}...")
            client = httpx.AsyncClient(timeout=180.0)
            payload = {"model": self.local_model, "prompt": prompt, "stream": False, "format": "json"}
            
            resp = await client.post(f"{url}/api/generate", json=payload)
            await client.aclose()
            
            if resp.status_code == 200:
                res = resp.json()
                print(f"DEBUG: Raw LLM Response: {str(res)[:200]}...") # Print snippet
                response_text = res.get("response", "[]")
                print(f"DEBUG: Extracted Text: {response_text[:200]}...")
                
                try:
                    data = json.loads(response_text)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        # Handle potential wrapper (results, sites, data, etc.)
                        for key in ["sites", "results", "data", "items"]:
                            if key in data and isinstance(data[key], list):
                                return data[key]
                        
                        # Fallback: if it has meaningful fields, treat as single item list
                        if "fqdn" in data or "category_main" in data:
                            return [data]
                        
                        print(f"DEBUG: Dictionary response but no known list key found. Keys: {list(data.keys())}")
                        return []
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")
                    return []
            else:
                print(f"Batch Request Failed: {resp.status_code} - {resp.text}")
                    
        except Exception as e:
             print(f"Local Batch LLM Failed: {e}")
        return []

    async def _analyze_with_local(self, title: str, content: str, category_definitions: Optional[Dict[str, str]]) -> Dict[str, Any]:
        import httpx
        url = self.get_base_url()
        if not url: return None
        client = httpx.AsyncClient(timeout=60.0)
        prompt = f"Analyze: {title}\n{content[:2000]}\nJSON Output keys: category_main, is_malicious, summary."
        payload = {"model": self.local_model, "prompt": prompt, "stream": False, "format": "json"}
        try:
            resp = await client.post(f"{url}/api/generate", json=payload)
            await client.aclose()
            if resp.status_code == 200:
                res = resp.json()
                return json.loads(res.get("response", "{}"))
        except:
            await client.aclose()
        return None

llm_service = LLMService()
