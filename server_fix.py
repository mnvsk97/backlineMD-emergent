# Temporary fix script
import re

with open('server.py', 'r') as f:
    content = f.read()

# Fix line 277 indentation
content = re.sub(r'        if expires_at > datetime\.now\(timezone\.utc\):\n        return cached\["payload"\]', 
                 '        if expires_at > datetime.now(timezone.utc):\n            return cached["payload"]', 
                 content)

# Fix line 544 indentation  
content = re.sub(r'        \}\n    \)\n\n    return payload\n    except Exception as e:', 
                 '        }\n        )\n\n        return payload\n    except Exception as e:', 
                 content)

with open('server.py', 'w') as f:
    f.write(content)

print("Fixed indentation")

