
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def test_bot_config():
    log("Testing /api/bot_config...")
    
    # GET config
    try:
        resp = requests.get(f"{BASE_URL}/api/bot_config")
        if resp.status_code != 200:
            log(f"GET /api/bot_config failed: {resp.text}", "ERROR")
            return False
        
        config = resp.json().get('config', {})
        log(f"Current config: {config}")
        
        # POST update
        new_config = {"execution_interval_seconds": 300}
        resp = requests.post(f"{BASE_URL}/api/bot_config", json=new_config)
        if resp.status_code != 200:
            log(f"POST /api/bot_config failed: {resp.text}", "ERROR")
            return False
            
        # Verify update
        resp = requests.get(f"{BASE_URL}/api/bot_config")
        updated_config = resp.json().get('config', {})
        if updated_config.get('execution_interval_seconds') != 300:
            log(f"Config update failed. Expected 300, got {updated_config.get('execution_interval_seconds')}", "ERROR")
            return False
            
        log("Bot config test passed", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Exception in test_bot_config: {e}", "ERROR")
        return False

def test_prompts():
    log("Testing /api/prompts...")
    
    # GET prompts
    try:
        resp = requests.get(f"{BASE_URL}/api/prompts?prompt_type=cooperative")
        if resp.status_code != 200:
            log(f"GET /api/prompts failed: {resp.text}", "ERROR")
            return False
            
        # POST new prompt
        new_prompt = {
            "prompt_type": "cooperative",
            "prompt_text": "Test cooperative prompt"
        }
        resp = requests.post(f"{BASE_URL}/api/prompts", json=new_prompt)
        if resp.status_code != 200:
            log(f"POST /api/prompts failed: {resp.text}", "ERROR")
            return False
        
        prompt_id = resp.json().get('id')
        log(f"Created prompt ID: {prompt_id}")
        
        # PUT update prompt (set active)
        update_data = {
            "prompt_type": "cooperative",
            "prompt_text": "Updated test prompt"
        }
        resp = requests.put(f"{BASE_URL}/api/prompts", json=update_data)
        if resp.status_code != 200:
            log(f"PUT /api/prompts failed: {resp.text}", "ERROR")
            return False
            
        log("Prompts test passed", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Exception in test_prompts: {e}", "ERROR")
        return False

def test_prompt_presets():
    log("Testing /api/prompt_presets...")
    
    try:
        # GET presets
        resp = requests.get(f"{BASE_URL}/api/prompt_presets")
        if resp.status_code != 200:
            log(f"GET /api/prompt_presets failed: {resp.text}", "ERROR")
            return False
            
        presets = resp.json().get('presets', [])
        log(f"Found {len(presets)} presets")
        
        # POST new preset (verification of bug)
        new_preset = {
            "name": "My Custom Preset",
            "prompt_type": "cooperative",
            "prompt_text": "Custom preset prompt"
        }
        resp = requests.post(f"{BASE_URL}/api/prompt_presets", json=new_preset)
        if resp.status_code != 200:
            log(f"POST /api/prompt_presets failed: {resp.text}", "ERROR")
            return False
            
        log("Check if preset name is persisted...")
        # GET again to see if it appears
        resp = requests.get(f"{BASE_URL}/api/prompt_presets")
        presets = resp.json().get('presets', [])
        found = any(p['name'] == "My Custom Preset" for p in presets)
        
        if not found:
            log("Preset name 'My Custom Preset' NOT found in GET response.", "ERROR")
            return False
        else:
            log("Preset name found!", "SUCCESS")
            
        # Test active preset
        # POST set active
        resp = requests.post(f"{BASE_URL}/api/prompt_presets/active", json={"preset_name": "hedging"})
        if resp.status_code != 200:
            log(f"POST /api/prompt_presets/active failed: {resp.text}", "ERROR")
            return False
            
        # GET active
        resp = requests.get(f"{BASE_URL}/api/prompt_presets/active")
        active = resp.json().get('active_preset')
        if active != "hedging":
            log(f"Active preset mismatch. Expected 'hedging', got '{active}'", "ERROR")
            return False
            
        log("Prompt presets active test passed", "SUCCESS")

        # Test updating custom preset via PUT /api/prompts
        log("Testing PUT /api/prompts with custom preset name...")
        update_custom_preset = {
            "prompt_type": "My Custom Preset",
            "prompt_text": "Updated custom preset text"
        }
        resp = requests.put(f"{BASE_URL}/api/prompts", json=update_custom_preset)
        if resp.status_code != 200:
            log(f"PUT /api/prompts (custom) failed: {resp.text}", "ERROR")
            return False
            
        # Verify it updated the actual preset definition
        resp = requests.get(f"{BASE_URL}/api/prompt_presets/preview/My Custom Preset")
        preview = resp.json()
        if preview.get('system_prompt') != "Updated custom preset text":
            log(f"Custom preset update verification failed. Got: {preview.get('system_prompt')}", "ERROR")
            return False
            
        log("Custom preset update test passed", "SUCCESS")
            
        return True

    except Exception as e:
        log(f"Exception in test_prompt_presets: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = True
    success &= test_bot_config()
    print("-" * 20)
    success &= test_prompts()
    print("-" * 20)
    success &= test_prompt_presets()
    
    if success:
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)
