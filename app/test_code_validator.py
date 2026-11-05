
from app.code_validator import validate_answer_code

# Test 1: Code that executes successfully
success_answer = '''
```python
print("Hello")
```
'''

# Test 2: Code with a runtime error
runtime_error_answer = '''
```python
print(10 / 0)
```
'''

# Test 3: Code with invalid syntax
syntax_error_answer = '''
```python
print("Hello"
```
'''

# Test 4: Code that exceeds the execution timeout
timeout_answer = '''
```python
while True:
    pass
```
'''

tests = [
    ("Successful execution", success_answer),
    ("Runtime error", runtime_error_answer),
    ("Invalid syntax", syntax_error_answer),
    ("Execution timeout", timeout_answer),
]

for test_name, answer in tests:
    print(f"\n--- {test_name} ---")
    print(validate_answer_code(answer))
