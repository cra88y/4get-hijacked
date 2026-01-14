import os
import re
import json

SCRAPER_DIR = "4get-repo/scraper"
OUTPUT_FILE = "4get_engine_specs.json"

# --- Regex Patterns ---
GET_PARAM_REGEX = re.compile(r'\$get\s*\[\s*["\']([a-zA-Z0-9_]+)["\']\s*\]')
FILTER_PARAM_REGEX = re.compile(r'^\s*["\']([a-zA-Z0-9_]+)["\']\s*=>\s*\[', re.MULTILINE)
FUNCTION_REGEX = re.compile(r"function\s+([a-zA-Z0-9_]+)\s*\(")

# --- Helpers ---

def extract_function_body(content, function_name):
    pattern = r"function\s+" + re.escape(function_name) + r"\s*\("
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return None
    
    start_index = match.end()
    open_brace_index = content.find('{', start_index)
    if open_brace_index == -1:
        return None
        
    brace_count = 1
    current_index = open_brace_index + 1
    while brace_count > 0 and current_index < len(content):
        char = content[current_index]
        if char == '{': brace_count += 1
        elif char == '}': brace_count -= 1
        current_index += 1
        
    body = content[open_brace_index+1:current_index-1]
    
    # Strip comments to prevent false positives
    body = re.sub(r'//.*', '', body)
    body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
    
    return body

def analyze_inputs(content):
    inputs = set()
    matches = GET_PARAM_REGEX.findall(content)
    for m in matches:
        inputs.add(m)

    getfilters_body = extract_function_body(content, "getfilters")
    if getfilters_body:
        filter_matches = FILTER_PARAM_REGEX.findall(getfilters_body)
        for m in filter_matches:
            inputs.add(m)
            
    return sorted(list(inputs))

def derive_capabilities(inputs):
    caps = {
        "paging": False,
        "time": False,
        "nsfw": False,
        "language": False,
        "country": False
    }
    
    if "npt" in inputs or "offset" in inputs or "cursor" in inputs:
        caps["paging"] = True
    if "time" in inputs or "date" in inputs or "newer" in inputs or "older" in inputs:
        caps["time"] = True
    if "nsfw" in inputs or "safe" in inputs or "safesearch" in inputs:
        caps["nsfw"] = True
    if "country" in inputs or "region" in inputs:
        caps["country"] = True
    if "lang" in inputs or "language" in inputs:
        caps["language"] = True
        
    return caps

def analyze_outputs(content):
    outputs = {}
    method_map = {
        "web": ["web", "image", "video", "news"],
        "image": ["image"],
        "video": ["video", "livestream", "reel"],
        "news": ["news"],
        "music": ["song", "album", "playlist", "podcast"]
    }

    for func_name, possible_categories in method_map.items():
        body = extract_function_body(content, func_name)
        if not body:
            continue
            
        for category in possible_categories:
            fields = analyze_output_assignment(body, category)
            if fields:
                if category not in outputs:
                    outputs[category] = fields
                else:
                    outputs[category].update(fields)
                    
    return outputs

def analyze_output_assignment(body, category):
    if f'"{category}"' not in body and f"'{category}'" not in body:
        return None
        
    fields = {}
    known_fields = ["title", "url", "description", "thumb", "date", "duration", "views", "author", "source"]
    
    for field in known_fields:
        # We look for "field" => ...
        # and try to check if it's set to null
        
        # Regex to find the key assignment
        # Matches: "title" =>
        pattern = r'["\']' + field + r'["\']\s*=>\s*([^,;\]]+)'
        matches = re.finditer(pattern, body)
        
        found_any = False
        is_supported = True
        
        for match in matches:
            found_any = True
            val = match.group(1).strip().lower()
            
            if val == 'null':
                is_supported = False
            elif val == '[]' or val == 'array()':
                is_supported = False
            
            if field == "thumb" and val.startswith('['):
                snippet_start = match.end()
                snippet = body[snippet_start:snippet_start+200]
                if re.search(r'["\']url["\']\s*=>\s*null', snippet, re.IGNORECASE):
                    is_supported = False

        if found_any:
            fields[field] = is_supported
            
    return fields if fields else None

def main():
    if not os.path.exists(SCRAPER_DIR):
        print(f"Error: {SCRAPER_DIR} not found.")
        return
        
    specs = {}
    
    files = sorted([f for f in os.listdir(SCRAPER_DIR) if f.endswith('.php')])
    print(f"Scanning {len(files)} engines...")
    
    for filename in files:
        engine_name = filename.replace('.php', '')
        filepath = os.path.join(SCRAPER_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            inputs = analyze_inputs(content)
            caps = derive_capabilities(inputs)
            outputs = analyze_outputs(content)
            
            specs[engine_name] = {
                "inputs": inputs,
                "capabilities": caps,
                "outputs": outputs
            }
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(specs, f, indent=2)
        
    print(f"Specs generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
