import llm
from llm.utils import (
    remove_dict_none_values,
    simplify_usage_dict,
)
import requests
from pydantic import Field, field_validator, model_validator
from typing import Optional, List, Dict, Any


@llm.hookimpl
def register_models(register):
    # Register available Exa models
    register(Exa("exa-search"))
    register(Exa("exa-search-contents"))
    register(Exa("exa-find-similar"))
    register(Exa("exa-answer"))


class ExaOptions(llm.Options):
    type: Optional[str] = Field(
        description="Search type: 'neural' (embeddings-based), 'keyword' (Google-like), or 'auto' (intelligently decides)",
        default="auto",
    )
    
    num_results: Optional[int] = Field(
        description="Number of results to return",
        default=5,
    )
    
    category: Optional[str] = Field(
        description="Filter results by data category (e.g., 'company', 'research paper', 'news')",
        default=None,
    )
    
    include_domains: Optional[List[str]] = Field(
        description="Domains to include in search",
        default=None,
    )
    
    exclude_domains: Optional[List[str]] = Field(
        description="Domains to exclude from search",
        default=None,
    )
    
    text: Optional[bool] = Field(
        description="Include full text content in response",
        default=True,
    )
    
    highlights: Optional[bool] = Field(
        description="Include relevant highlights in response",
        default=False,
    )
    
    summary: Optional[bool] = Field(
        description="Include generated summary in response",
        default=False,
    )
    
    stream: Optional[bool] = Field(
        description="Stream the response for answer endpoint",
        default=True,
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, search_type):
        if search_type not in ("neural", "keyword", "auto"):
            raise ValueError("type must be one of 'neural', 'keyword', or 'auto'")
        return search_type
    
    @field_validator("num_results")
    @classmethod
    def validate_num_results(cls, num_results):
        if num_results <= 0:
            raise ValueError("num_results must be greater than 0")
        return num_results


class Exa(llm.Model):
    needs_key = "exa"
    key_env_var = "LLM_EXA_KEY"
    can_stream = True
    base_url = "https://api.exa.ai"

    class Options(ExaOptions):
        pass

    def __init__(self, model_id):
        self.model_id = model_id

    def execute(self, prompt, stream, response, conversation):
        api_key = self.get_key()
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
        }
        
        # Process based on model type (exa-search, exa-search-contents, exa-find-similar, exa-answer)
        if self.model_id == "exa-search":
            result = self.handle_search(prompt, headers)
            response.response_json = remove_dict_none_values(result)
            self.format_search_results(result, response)
            yield self.format_search_output(result)
            
        elif self.model_id == "exa-search-contents":
            result = self.handle_search_contents(prompt, headers)
            response.response_json = remove_dict_none_values(result)
            self.format_search_contents_results(result, response)
            yield self.format_search_contents_output(result)
            
        elif self.model_id == "exa-find-similar":
            result = self.handle_find_similar(prompt, headers)
            response.response_json = remove_dict_none_values(result)
            self.format_find_similar_results(result, response)
            yield self.format_find_similar_output(result)
            
        elif self.model_id == "exa-answer":
            if stream and prompt.options.stream:
                yield from self.handle_answer_stream(prompt, headers, response)
            else:
                result = self.handle_answer(prompt, headers)
                response.response_json = remove_dict_none_values(result)
                self.format_answer_results(result, response)
                yield self.format_answer_output(result)

    def handle_search(self, prompt, headers):
        params = {
            "query": prompt.prompt,
            "numResults": prompt.options.num_results,
            "type": prompt.options.type,
        }
        
        if prompt.options.category:
            params["category"] = prompt.options.category
            
        if prompt.options.include_domains:
            params["includeDomains"] = prompt.options.include_domains
            
        if prompt.options.exclude_domains:
            params["excludeDomains"] = prompt.options.exclude_domains
        
        response = requests.post(
            f"{self.base_url}/search",
            headers=headers,
            json=params
        )
        
        if response.status_code != 200:
            raise llm.ModelError(f"Exa API error: {response.status_code} {response.text}")
            
        return response.json()
    
    def handle_search_contents(self, prompt, headers):
        # First perform search
        search_result = self.handle_search(prompt, headers)
        
        # Extract URLs from search results
        urls = [result["url"] for result in search_result.get("results", [])]
        
        if not urls:
            return {"results": [], "message": "No search results found"}
        
        # Now get contents for those URLs
        params = {
            "urls": urls,
        }
        
        if prompt.options.text:
            params["text"] = True
            
        if prompt.options.highlights:
            params["highlights"] = True
            
        if prompt.options.summary:
            params["summary"] = True
        
        response = requests.post(
            f"{self.base_url}/contents",
            headers=headers,
            json=params
        )
        
        if response.status_code != 200:
            raise llm.ModelError(f"Exa API error: {response.status_code} {response.text}")
            
        content_result = response.json()
        
        # Combine search results with content results
        return {
            "search": search_result,
            "contents": content_result
        }
    
    def handle_find_similar(self, prompt, headers):
        # Assume prompt is a URL
        params = {
            "url": prompt.prompt.strip(),
            "numResults": prompt.options.num_results,
        }
        
        if prompt.options.exclude_domains:
            params["excludeDomains"] = prompt.options.exclude_domains
        
        response = requests.post(
            f"{self.base_url}/findSimilar",
            headers=headers,
            json=params
        )
        
        if response.status_code != 200:
            raise llm.ModelError(f"Exa API error: {response.status_code} {response.text}")
            
        return response.json()
    
    def handle_answer(self, prompt, headers):
        params = {
            "query": prompt.prompt,
        }
        
        if prompt.options.text:
            params["text"] = True
        
        response = requests.post(
            f"{self.base_url}/answer",
            headers=headers,
            json=params
        )
        
        if response.status_code != 200:
            raise llm.ModelError(f"Exa API error: {response.status_code} {response.text}")
            
        return response.json()
    
    def handle_answer_stream(self, prompt, headers, response):
        params = {
            "query": prompt.prompt,
        }
        
        if prompt.options.text:
            params["text"] = True
        
        with requests.post(
            f"{self.base_url}/answer",
            headers=headers,
            json=params,
            stream=True
        ) as resp:
            if resp.status_code != 200:
                raise llm.ModelError(f"Exa API error: {resp.status_code} {resp.text}")
                
            # Initialize response data
            response_data = {"answer": "", "citations": []}
            
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    # Process chunk - in a real implementation you'd need to
                    # handle Server-Sent Events (SSE) correctly
                    chunk_text = chunk.decode('utf-8')
                    response_data["answer"] += chunk_text
                    yield chunk_text
            
            # Store the complete response
            response.response_json = remove_dict_none_values(response_data)
            
            # Format citations if any
            if "citations" in response_data and response_data["citations"]:
                yield "\n\n## Citations:\n"
                for i, citation in enumerate(response_data["citations"], 1):
                    yield f"[{i}] {citation['url']}\n"
    
    def format_search_results(self, result, response):
        # Set usage information if available
        if "executionTime" in result:
            response.set_usage(
                input=0, 
                output=0, 
                details={"execution_time": result["executionTime"]}
            )
    
    def format_search_output(self, result):
        output = f"# Exa Search Results\n\n"
        
        if "results" not in result or not result["results"]:
            return output + "No results found."
        
        for i, res in enumerate(result["results"], 1):
            output += f"## {i}. {res.get('title', 'No title')}\n"
            output += f"URL: {res.get('url', 'No URL')}\n\n"
            
            if "text" in res and res["text"]:
                snippet = res["text"][:300] + "..." if len(res["text"]) > 300 else res["text"]
                output += f"{snippet}\n\n"
        
        if "executionTime" in result:
            output += f"\nExecution time: {result['executionTime']:.2f}s"
            
        if "totalResults" in result:
            output += f"\nTotal results available: {result['totalResults']}"
            
        return output
    
    def format_search_contents_results(self, result, response):
        # Similar to search results, but with content information
        if "search" in result and "executionTime" in result["search"]:
            response.set_usage(
                input=0, 
                output=0, 
                details={"execution_time": result["search"]["executionTime"]}
            )
    
    def format_search_contents_output(self, result):
        output = f"# Exa Search & Contents Results\n\n"
        
        if "search" not in result or "results" not in result["search"] or not result["search"]["results"]:
            return output + "No results found."
        
        if "contents" not in result or not result["contents"]:
            return output + "No content available for the results."
        
        for i, res in enumerate(result["search"]["results"], 1):
            output += f"## {i}. {res.get('title', 'No title')}\n"
            output += f"URL: {res.get('url', 'No URL')}\n\n"
            
            # Find matching content
            content = next((c for c in result["contents"] if c.get("url") == res.get("url")), None)
            
            if content:
                if "text" in content and content["text"]:
                    text = content["text"]
                    # Limit text length for readability
                    if len(text) > 1000:
                        text = text[:1000] + "...\n[Text truncated]"
                    output += f"### Content:\n{text}\n\n"
                
                if "summary" in content and content["summary"]:
                    output += f"### Summary:\n{content['summary']}\n\n"
                
                if "highlights" in content and content["highlights"]:
                    output += f"### Highlights:\n"
                    for highlight in content["highlights"]:
                        output += f"- {highlight}\n"
                    output += "\n"
        
        return output
    
    def format_find_similar_results(self, result, response):
        # Set usage information if available
        if "executionTime" in result:
            response.set_usage(
                input=0, 
                output=0, 
                details={"execution_time": result["executionTime"]}
            )
    
    def format_find_similar_output(self, result):
        output = f"# Exa Similar Results\n\n"
        output += f"Finding similar pages to: {result.get('url', 'No URL')}\n\n"
        
        if "results" not in result or not result["results"]:
            return output + "No similar results found."
        
        for i, res in enumerate(result["results"], 1):
            output += f"## {i}. {res.get('title', 'No title')}\n"
            output += f"URL: {res.get('url', 'No URL')}\n"
            
            if "score" in res:
                output += f"Similarity Score: {res['score']:.2f}\n"
                
            if "text" in res and res["text"]:
                snippet = res["text"][:300] + "..." if len(res["text"]) > 300 else res["text"]
                output += f"\n{snippet}\n\n"
        
        return output
    
    def format_answer_results(self, result, response):
        # Set usage information if available
        if "executionTime" in result:
            response.set_usage(
                input=0, 
                output=0, 
                details={"execution_time": result["executionTime"]}
            )
    
    def format_answer_output(self, result):
        output = ""
        
        if "answer" in result and result["answer"]:
            output += result["answer"]
        else:
            return "No answer was generated."
        
        if "citations" in result and result["citations"]:
            output += "\n\n## Citations:\n"
            for i, citation in enumerate(result["citations"], 1):
                output += f"[{i}] {citation.get('url', 'No URL')}\n"
        
        return output

    def __str__(self):
        return f"Exa: {self.model_id}"
