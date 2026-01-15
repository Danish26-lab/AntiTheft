#!/usr/bin/env python3
"""
Test script to verify password extraction from activity log descriptions
"""

# Test cases
test_cases = [
    "Remote lock action triggered by user. password: Danish26",
    "Remote lock action triggered by user. password: Danish26, Message: Test message",
    "Remote lock action triggered by user. password: Danish26, Message: Hello world",
    "Remote lock action triggered by user. password: antitheft2024",
    "Remote lock action triggered by user. password: test123, Message: Some message here",
]

def extract_password(desc):
    """Extract password from description using the same logic as agent.py"""
    if 'password:' not in desc:
        return None
    
    parts = desc.split('password:')
    if len(parts) > 1:
        password_part = parts[1].strip()
        print(f"  Raw password part: '{password_part}'")
        
        if ',' in password_part:
            lock_password = password_part.split(',')[0].strip()
        else:
            lock_password = password_part.split()[0] if password_part else None
        
        if lock_password:
            lock_password = lock_password.rstrip(',. ;:')
            lock_password = lock_password.strip()
        
        return lock_password
    return None

print("Testing password extraction:\n")
for i, desc in enumerate(test_cases, 1):
    print(f"Test {i}: {desc}")
    password = extract_password(desc)
    print(f"  Extracted: '{password}' (length: {len(password) if password else 0})")
    print()

