import os
import urllib.request
import urllib.error

env_vars = {}
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                env_vars[k] = v

gemini_key = env_vars.get('GEMINI_API_KEY', '')
groq_key = env_vars.get('GROQ_API_KEY', '')

print('--- Testing Gemini ---')
if not gemini_key or 'your_gemini' in gemini_key:
    print('Gemini Key is missing or default.')
else:
    try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}'
        req = urllib.request.Request(url, data=b'{"contents":[{"parts":[{"text":"Say OK"}]}]}', headers={'Content-Type': 'application/json'}, method='POST')
        resp = urllib.request.urlopen(req)
        print('Gemini API: SUCCESS! (Code 200)')
    except urllib.error.HTTPError as e:
        print(f'Gemini API Error: {e.code} - {e.read().decode()}')

print('\n--- Testing Groq ---')
if not groq_key or 'your_groq' in groq_key:
    print('Groq Key is missing or default.')
else:
    try:
        req = urllib.request.Request('https://api.groq.com/openai/v1/chat/completions', data=b'{"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "Say OK"}]}', headers={'Authorization': f'Bearer {groq_key}', 'Content-Type': 'application/json'}, method='POST')
        resp = urllib.request.urlopen(req)
        print('Groq API: SUCCESS! (Code 200)')
    except urllib.error.HTTPError as e:
        print(f'Groq API Error: {e.code} - {e.read().decode()}')
