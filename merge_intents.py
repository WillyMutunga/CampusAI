import json
import os
import shutil

def merge_datasets(original_file='intents.json', new_file='model.json', output_file='intents.json'):
    # 1. Backup original file
    if os.path.exists(original_file):
        shutil.copy(original_file, original_file + '.bak')
        print(f"Backed up {original_file} to {original_file}.bak")
    
    # 2. Load original intents
    try:
        with open(original_file, 'r') as f:
            original_data = json.load(f)
            original_intents = original_data.get('intents', [])
    except FileNotFoundError:
        original_intents = []
        original_data = {'intents': []}

    # 3. Load new dataset
    try:
        with open(new_file, 'r') as f:
            new_data = json.load(f)
            # Handle different structures if necessary
            if 'intents' in new_data:
                new_intents = new_data['intents']
            else:
                # Assume it's a list of intents directly
                new_intents = new_data
    except FileNotFoundError:
        print(f"Error: {new_file} not found.")
        return

    print(f"Loaded {len(original_intents)} existing intents.")
    print(f"Loaded {len(new_intents)} new intents to merge.")

    # 4. Merge Logic
    # We want to add new intents. If an intent with the same tag exists, we can append patterns/responses
    # or skip it. Let's append unique patterns and responses.
    
    existing_tags = {i['tag']: i for i in original_intents}
    
    added_count = 0
    merged_count = 0

    for new_intent in new_intents:
        # Map fields from model.json to intents.json format
        # model.json: intent, text, responses
        # intents.json: tag, patterns, responses
        
        tag = new_intent.get('intent') or new_intent.get('tag')
        patterns = new_intent.get('text') or new_intent.get('patterns', [])
        responses = new_intent.get('responses', [])
        
        if not tag:
            continue

        if tag in existing_tags:
            # Merge
            existing = existing_tags[tag]
            
            # Add unique patterns
            for p in patterns:
                if p not in existing['patterns']:
                    existing['patterns'].append(p)
            
            # Add unique responses
            for r in responses:
                if r not in existing['responses']:
                    existing['responses'].append(r)
            
            merged_count += 1
        else:
            # Add new intent
            new_entry = {
                'tag': tag,
                'patterns': patterns,
                'responses': responses
            }
            original_intents.append(new_entry)
            existing_tags[tag] = new_entry # Update map so we don't add duplicates from the new file itself if any
            added_count += 1

    # 5. Save merged data
    original_data['intents'] = original_intents
    
    with open(output_file, 'w') as f:
        json.dump(original_data, f, indent=2)
    
    print(f"Merge complete. Added {added_count} new intents. Merged {merged_count} existing intents.")
    print(f"Total intents now: {len(original_intents)}")

if __name__ == "__main__":
    merge_datasets()
