import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

sql = """DELETE FROM config WHERE key = 'ADMIN_CHAT_ID';
DELETE FROM students;
DELETE FROM transactions;
DELETE FROM config WHERE key = 'language';"""

r = requests.post('http://127.0.0.1:10086/command', json={
    'action': 'evaluate',
    'args': {
        'code': f'''
            (function() {{
                // Try Monaco editor API
                if (typeof monaco !== 'undefined' && monaco.editor) {{
                    var models = monaco.editor.getModels();
                    if (models.length > 0) {{
                        models[0].setValue({json.dumps(sql)});
                        return JSON.stringify({{success: true, method: 'monaco'}});
                    }}
                }}
                // Fallback: find textarea in editor
                var ta = document.querySelector('textarea');
                if (ta) {{
                    ta.value = {json.dumps(sql)};
                    ta.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return JSON.stringify({{success: true, method: 'textarea'}});
                }}
                return JSON.stringify({{success: false, reason: 'no editor found'}});
            }})()
        '''
    },
    'session': 'supabase-reset'
})
print(r.text)
