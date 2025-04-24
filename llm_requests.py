import json
import uuid
import os
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import litellm  # Import litellm for handling model requests
from openai import OpenAI
import pytz
from constants import constants
from backend_interaction import send_to_backend


default_model = "gpt-4o" 

# Create a ThreadPoolExecutor for parallel LLM requests
LLM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def track_cost_callback(kwargs, completion_response, start_time, end_time):
    try:
        response_cost = kwargs.get("response_cost", 0)
        print("Streaming response cost:", response_cost)
    except Exception as e:
        print("Error tracking cost:", e)

# Set the custom callback for litellm
litellm.success_callback = [track_cost_callback]


def get_llm_response(message, model: str = None):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        #temperature=0,
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": message}
        ]
    )

    data = response.choices[0].message.content
    clean_data = data.replace("```", "").replace("json", "").strip()
    
    try:
        final_response = json.loads(clean_data)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response received: {clean_data}")
        raise ValueError(f"Failed to parse JSON: {e}")
    
    # Extract token usage information
    tokens_used = response.usage.total_tokens
    
    spend = {
        "id": str(uuid.uuid4()),
        "transactionDate": datetime.now(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": model,
        "spend": tokens_used * 0.00250 / 1000,
    }
    
    spend['sourceEmailId'] = constants['SOURCING_ID']
    spend['testId'] = constants['TEST_ID']
    send_to_backend(data=spend, path=f'spend')

    print('done getting llm response')
    
    return final_response


def _get_llm_response_parallel(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function for parallel LLM requests"""
    try:
        message = request_data.get('message', '')
        model = request_data.get('model', default_model)
        request_id = request_data.get('id', str(uuid.uuid4()))
        
        # Get the response using the existing function
        response = get_llm_response(message, model)
        
        return {
            'id': request_id,
            'status': 'success',
            'data': response
        }
    except Exception as e:
        return {
            'id': request_id,
            'status': 'error',
            'error': str(e)
        }


def get_llm_responses_parallel(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Execute multiple LLM requests in parallel using true asynchronous execution
    
    Args:
        requests: List of dictionaries with the following keys:
            - message: The message to send to the LLM
            - model: The model to use (optional)
            - id: Optional identifier to track the request
    
    Returns:
        List of response dictionaries with original request ID, status and data
    """
    if not requests:
        return []
        
    # Increase max_workers for the global executor based on request count
    max_workers = min(len(requests) * 2, 20)  # Scale based on requests but cap at 20
    
    # Create a dedicated thread pool for this batch of requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as batch_executor:
        # Submit all requests to the executor at once
        print(f"Submitting {len(requests)} parallel LLM requests...")
        futures_dict = {
            batch_executor.submit(_get_llm_response_parallel, req): req.get('id', str(uuid.uuid4()))
            for req in requests
        }
        
        # Process results as they complete using as_completed for true asynchronous behavior
        results = []
        for future in concurrent.futures.as_completed(futures_dict):
            req_id = futures_dict[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error in parallel LLM request {req_id}: {str(e)}")
                results.append({
                    'id': req_id,
                    'status': 'error',
                    'error': str(e)
                })
                
        print(f"Completed {len(results)}/{len(requests)} parallel LLM requests")
        return results

