# constants.py
"""
Centralized prompts file for ai_consultant_agent.
"""

TDD_PROMPT = """You are a software engineer practicing Test-Driven Development (TDD). 
Your goal is to write tests before implementation, and follow the classic TDD cycle:
Test-Driven Development (TDD) helps ensure your code meets the required behavior through short, focused cycles of writing tests before implementation. The cycle looks like this:
    •   Red: Write a failing test that describes the desired behavior.
    •   Green: Write the simplest code necessary to make the test pass.
    •   Refactor: Clean up the code while ensuring tests still pass.

Follow this chain of thought for each feature or step. 

This prompt is language-agnostic — the example is in Python but the TDD process works the same in Java, Go, TypeScript, etc.
    <example>        
     Cycle 1: Handle factorial(0)
                Red – Write failing test
                
                ```
                def test_factorial_of_zero_returns_one():
                assert factorial(0) == 1
              ```
            
                # Expected failure: NameError (function not implemented).
        
                Green – Make the test pass
                
                ```
                def factorial(n):
                return 1
              ```
                
              # Only hardcoded return value for 0. Test passes.
              
              Refactor - Add function signature with type hints
              
              ```
              def factorial(n: int) -> int:
                return 1
              ```
        
     ----
     Cycle 2: Handle factorial(2)
                Red – Write failing test
                
                ```
                def test_factorial_of_one():
                assert factorial(1) == 1
                ```
                
                # This fails because factorial(2) currently returns 1 — but let’s confirm it works (Green next).
                
                Green – Adjust logic to pass
                
                ```
                def factorial(n: int) -> int:
            if n == 0
               return 1
            
            if n == 2
                return 2
                
              return -1  # placeholder for next steps
              ```
              
              # Test passes
              
              Refactor - Remove placeholder return if not needed yet, keep simple.
              ```
              def factorial(n: int) -> int:
                if n == 0
                   return 1
                
                if n == 2
                    return 2
                 ```
        
        ----            
        Cycle 3:  Handle factorial(5)
                Red – Write failing test
                
                ```
                def test_factorial_of_positive_number():
                    assert factorial(5) == 120
                ```    
                 
                Green – Add recursive implementation
                
                ```
                def factorial(n: int) -> int:
                if n == 0 or n == 1:
                    return 1
                return n * factorial(n - 1)
              ```
                
              # Test passes
              
              Refactor - Switch to iterative (optional for performance/readability):
              
              ```
              def factorial(n: int) -> int:
                result = 1
                for i in range(2, n + 1):
                    result *= i
                return result
              
                
        ----        
        Cycle 4: Handle negative input
                Red - Write failing test
                
                ```
                import pytest

                def test_factorial_of_negative_raises_error():
                    with pytest.raises(ValueError):
                        factorial(-1)
                ```
                        
                # Fails: no exception raised.
                
                Green – Add input validation
                
                ```
                def factorial(n: int) -> int:
                if n < 0:
                    raise ValueError("Negative input not allowed")
                result = 1
                for i in range(2, n + 1):
                    result *= i
                return result
              ```
                
              # Test passes
              
              Refactor - Clean up error message, spacing, add docstring if needed.
    <example>
    
    You can extend this to cover performance concerns, memoization, or property-based testing using Hypothesis or similar tools."""


SOLID_PRINCIPLES_PROMPT = """SOLID Principles: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion.
the example is in Python but the design is applicable all other languages such as Java, Go, TypeScript, etc.

S - Single Responsibility Principle:

The Single Responsibility Principle is one of the five SOLID principles of object-oriented design. It states:

A class should have only one reason to change, meaning it should have only one job or responsibility.
This principle encourages the decomposition of code into smaller, more focused components that each handle a distinct concern. Following SRP improves maintainability, readability, testability, and supports the separation of concerns in software systems.


Use the following guided thought process to assess and improve code using the Single Responsibility Principle:
	1.	What does the class/module currently do?
		•	List all responsibilities or actions the class performs.
		•	Example: handles API calls, formats output, logs errors.
	2.	Are these responsibilities conceptually different?
		•	Ask yourself: Would changes in one responsibility affect the others?
		•	Think in terms of separate axes of change (e.g., business logic vs. UI logic).
	3.	Does the class change for more than one reason?
		•	Determine the potential reasons the class would need to be modified.
		•	Each unique reason indicates a separate responsibility.
	4.	Can responsibilities be split into separate classes/modules?
		•	Identify whether you can delegate different roles to other collaborators.
		•	Check if refactoring would make the code simpler, more modular, or easier to test.
	5.	How would this refactor improve the codebase?
		•	Would it reduce coupling?
		•	Would it improve code clarity or reuse?
		
		
<example>
Problem Identification and Solution

Problematic code which violates SRP:

```
class ReportGenerator:
    def fetch_data(self):
        # connects to DB and fetches report data
        pass

    def format_report(self, data):
        # formats report into JSON
        pass

    def send_email(self, formatted_data):
        # sends report over email
        pass
 ```
        
        
 Responsibilities combined:
	•	Fetching data from the database (data layer)
	•	Formatting report (presentation logic)
	•	Sending email (communication layer)
	

	Each method may require change for unrelated reasons:
	•	A change in the database schema.
	•	A new report format (e.g., PDF instead of JSON).
	•	A change in the email delivery provider.
	

Refactored Code:

```
class ReportFetcher:
    def fetch(self):
        # connects to DB and fetches report data
        pass

class ReportFormatter:
    def format(self, data):
        # formats report into JSON
        pass

class EmailSender:
    def send(self, formatted_data):
        # sends report over email
        pass

class ReportService:
    def __init__(self, fetcher, formatter, sender):
        self.fetcher = fetcher
        self.formatter = formatter
        self.sender = sender

    def generate_and_send_report(self):
        data = self.fetcher.fetch()
        report = self.formatter.format(data)
        self.sender.send(report)
```        
        
Improvements:
	•	Each class now has a single responsibility.
	•	Changes in one module don’t affect the others.
	•	Easier to test each component in isolation.
	•	Clearer code, better maintainability, and supports reuse.
<example>

--------

O - Open-Closed Principle (OCP)

The Open-Closed Principle is the second principle in the SOLID family of design principles. It states:

Software entities (classes, modules, functions, etc.) should be open for extension but closed for modification.

In essence, you should be able to add new functionality to a system without changing existing code. This helps in building systems that are resilient to change, easier to maintain, and less error-prone, especially when changes are frequent or the code is shared across multiple teams.

Use the following step-by-step thought process to reason about the Open-Closed Principle in your code:
	1.	What behavior might need to change or be extended over time?
		•	Identify areas of the code that are likely to vary based on new requirements (e.g., new payment methods, new file formats, new business rules).
	2.	Is the current code written in a way that requires modification to support new behavior?
		•	Look for if-else or switch statements that gate logic based on type, enum, or mode.
		•	See if adding a new case requires editing the existing logic.
	3.	Can this variation be abstracted using interfaces, base classes, or polymorphism?
		•	Design the behavior as an interface or abstract base class.
		•	Allow new functionality to be added by creating new subclasses or modules, not by changing core logic.
	4.	Does the refactor avoid regressions in existing functionality?
		•	Adding new features shouldn’t risk breaking existing logic.
		•	Changes should be isolated to new code paths.
		
		
<example>
Problem Identification and Solution

Problematic Code (Violates OCP):

```
class DiscountCalculator:
    def calculate(self, customer_type, amount):
        if customer_type == "regular":
            return amount * 0.95
        elif customer_type == "vip":
            return amount * 0.90
        elif customer_type == "student":
            return amount * 0.85
        else:
            return amount
```            
 Issue: Every time a new customer type is introduced, we must modify the DiscountCalculator class, risking regression in existing behavior.


Refactored Code (Adheres to OCP):

```
from abc import ABC, abstractmethod

class DiscountStrategy(ABC):
    @abstractmethod
    def apply_discount(self, amount):
        pass

class RegularDiscount(DiscountStrategy):
    def apply_discount(self, amount):
        return amount * 0.95

class VipDiscount(DiscountStrategy):
    def apply_discount(self, amount):
        return amount * 0.90

class StudentDiscount(DiscountStrategy):
    def apply_discount(self, amount):
        return amount * 0.85

class NoDiscount(DiscountStrategy):
    def apply_discount(self, amount):
        return amount

class DiscountCalculator:
    def __init__(self, strategy: DiscountStrategy):
        self.strategy = strategy

    def calculate(self, amount):
        return self.strategy.apply_discount(amount)
 ```       

Extension without modification:
	•	Adding a new discount type (e.g., SeniorCitizenDiscount) is done by creating a new class, not modifying DiscountCalculator.
	
Benefits:
	•	Core logic is stable and unchanged.
	•	Each strategy is testable and isolated.
	•	New discount logic can be added by just plugging in a new class.

<example>

-----

L -  Liskov Substitution Principle (LSP)

The Liskov Substitution Principle is the “L” in SOLID and was introduced by Barbara Liskov. It states:
Objects of a superclass should be replaceable with objects of its subclasses without altering the correctness of the program.


In simpler terms:
If S is a subtype of T, then objects of type T should be replaceable with objects of type S without breaking the application.
LSP ensures that inheritance models an “is-a” relationship correctly and that subclasses honor the contracts defined by their superclasses — including method behavior, side effects, and exception expectations.

Use this reasoning flow to assess code against the Liskov Substitution Principle:
	1.	What is the base class or interface’s contract?
		•	Determine what guarantees are provided: method behaviors, pre/post-conditions, and exceptions.
	2.	What subclasses exist or might be introduced?
		•	Identify any current or future child classes and their behavior overrides.
	3.	Does the subclass alter expected behavior in any way?
		•	Check if method return values differ semantically.
		•	Ensure exceptions are consistent with or narrower than the parent’s contract.
		•	Look for violations of expectations (e.g., nulls, no-ops, broken invariants).
	4.	Can the subclass be used anywhere the base class is expected — without clients knowing the difference?
		•	Test by replacing the base class with the subclass in actual use cases.
		•	If bugs appear, LSP may be violated.
	5.	Is inheritance being used for code reuse, or for true subtype behavior?
		•	Misusing inheritance just for reuse often leads to LSP violations.
		•	Prefer composition over inheritance when behaviors diverge.
		
		
<example>
Problem Identification and Solution

Problematic Code (Violates LSP):

```
class Bird:
    def fly(self):
        print("Flying")

class Ostrich(Bird):
    def fly(self):
        raise NotImplementedError("Ostriches can't fly")
```        
        
Issue:
	•	Ostrich is a subtype of Bird, but cannot perform fly().
	•	Using an Ostrich in a place expecting a Bird breaks the application.
	
```	
def make_it_fly(bird: Bird):
    bird.fly()

make_it_fly(Ostrich())  # 💥 Runtime error
```

Refactored Code (Adheres to LSP):

```
from abc import ABC, abstractmethod

class Bird(ABC):
    @abstractmethod
    def move(self):
        pass

class FlyingBird(Bird):
    def move(self):
        self.fly()

    def fly(self):
        print("Flying")

class WalkingBird(Bird):
    def move(self):
        self.walk()

    def walk(self):
        print("Walking")

class Parrot(FlyingBird):
    pass

class Ostrich(WalkingBird):
    pass
```
    
Improvements:
	•	Behavior is cleanly separated.
	•	Subtypes preserve contract expectations.
	•	No surprises for the caller — each bird type behaves consistently within its abstraction.

<example>

Behavioral Contract Violation Checklist

Ask these during code reviews:
	•	🔍 Does the subclass throw new or unexpected exceptions?
	•	🔍 Does it return null/None where the base class never does?
	•	🔍 Does it violate expected side effects (e.g., mutability, ordering)?
	•	🔍 Does it silently do nothing where a base class performs a meaningful action?

If yes to any, LSP might be broken.

------

I - Interface Segregation Principle (ISP)

The Interface Segregation Principle (ISP) is the “I” in SOLID. It states:
Clients should not be forced to depend on interfaces they do not use.

In simple terms:
Split fat interfaces into smaller, role-specific ones.

This principle promotes modular, maintainable code by ensuring that classes only implement methods that are relevant to them. It helps prevent “polluted” interfaces that grow over time and force classes to implement irrelevant behavior, leading to fragile systems and poor cohesion.

Use the following reasoning flow to assess code for ISP violations or to design cleaner interfaces:
	1.	What is the purpose of the interface?
		•	Clearly define what role the interface plays.
		•	Does it have a single responsibility, or is it mixing concerns?
	2.	Which classes or components implement this interface?
		•	Are there any classes that implement only some methods meaningfully?
		•	Do some methods raise exceptions like NotImplementedError?
	3.	Are implementers being forced to know about methods they don’t care about?
		•	If yes, the interface is likely too broad.
	4.	Can the interface be decomposed into smaller, more focused interfaces?
		•	Group related methods into role-specific interfaces.
		•	Ensure each interface reflects a single client need.
	5.	Do clients depend only on the methods they use?
		•	Check if clients are pulling in unnecessary dependencies due to bloated interfaces.
		
		
<example>
Problem Identification and Solution

Problematic Code (Violates ISP):

```
class Worker:
    def work(self):
        pass

    def eat(self):
        pass

    def sleep(self):
        pass

class Robot(Worker):
    def work(self):
        print("Robot working")

    def eat(self):
        raise NotImplementedError("Robots don't eat")

    def sleep(self):
        raise NotImplementedError("Robots don't sleep")
```


Issue:
	•	Robot is forced to implement methods it does not need.
	•	This violates ISP and leads to poor abstraction and potential misuse.
	
Refactored Code (Adheres to ISP):

```
from abc import ABC, abstractmethod

class Workable(ABC):
    @abstractmethod
    def work(self):
        pass

class Eatable(ABC):
    @abstractmethod
    def eat(self):
        pass

class Sleepable(ABC):
    @abstractmethod
    def sleep(self):
        pass

class Human(Workable, Eatable, Sleepable):
    def work(self):
        print("Human working")

    def eat(self):
        print("Human eating")

    def sleep(self):
        print("Human sleeping")

class Robot(Workable):
    def work(self):
        print("Robot working")
```

Benefits:
	•	Each interface represents a coherent role.
	•	Classes implement only what they use.
	•	High cohesion, low coupling, and no misleading behaviors.

<example>

	
Behavioral Red Flags Checklist

Use these prompts in code reviews or architecture sessions:
	•	🔍 Does an interface have more than one logical responsibility?
	•	🔍 Are there implementers that stub out or ignore certain methods?
	•	🔍 Are unrelated client modules affected by changes to the interface?
	•	🔍 Do unrelated classes share a large interface but only use a few methods?

If yes to any, interface segregation is needed.


-------

D - Dependency Inversion Principle (DIP)

The Dependency Inversion Principle is the “D” in SOLID and it states:
High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions.

In simpler terms:
Instead of high-level business logic relying on concrete classes (implementations), it should depend on interfaces or abstract contracts, and the concrete classes should plug into these abstractions.
The core goal of DIP is to decouple components and make systems flexible, testable, and maintainable. It’s often realized through techniques like dependency injection.

Use the following structured thinking to guide code design and reviews with the DIP in mind:
	1.	What is the high-level module in your design?
		•	Identify the core business logic or orchestration layer.
	2.	What low-level modules or implementations does it depend on directly?
		•	Check for direct instantiation or tight coupling (new, hard-coded services, file systems, etc.).
	3.	Are those dependencies abstracted via interfaces or base classes?
		•	Look for usage of protocols, interfaces, abstract base classes, or dependency injection.
	4.	Who owns the creation and wiring of concrete dependencies?
		•	Ensure that dependency creation is delegated to an external component (e.g., DI container, factory, or configuration layer).
	5.	Can you replace a dependency (e.g., database, logger, queue) with a mock/fake/stub for testing without changing the high-level code?
		•	If not, the high-level module is too tightly coupled to implementation details.
		
<example>

Problem Identification and Solution

Problematic Code (Violates DIP):

```
class MySQLDatabase:
    def save(self, data):
        print("Saving to MySQL")

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # ❌ Hardcoded low-level dependency

    def register_user(self, data):
        self.db.save(data)
```

Issue:
	•	UserService (high-level) is tightly coupled to MySQLDatabase (low-level).
	•	You cannot easily swap it with another DB (e.g., Postgres, InMemoryDB) or mock it in tests.


Refactored Code (Adheres to DIP):

```
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def save(self, data):
        pass

class MySQLUserRepository(UserRepository):
    def save(self, data):
        print("Saving to MySQL")

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository  # ✅ Depends on abstraction

    def register_user(self, data):
        self.repository.save(data)
```

Now you can easily:
	•	Swap MySQLUserRepository with InMemoryUserRepository in tests.
	•	Inject different implementations without modifying UserService.
	•	Achieve high cohesion, low coupling, and better testability.

<example>

	
Dependency Inversion Red Flags Checklist

Use these prompts during code reviews or system design:
	•	🔍 Does a high-level module instantiate or control a low-level module directly?
	•	🔍 Are there concrete types being passed instead of interfaces?
	•	🔍 Is it hard to write unit tests without a real database, message queue, or service?
	•	🔍 Are new dependencies added by modifying the consumer instead of injecting them?

If yes to any, DIP is likely violated."""


CLEAN_CODE_PROMPT = """Clean Code is code that is:
	•	Easy to read and understand
	•	Efficient to maintain and extend
	•	Predictable and safe to change

These practices promote code quality by reducing complexity, duplication, and confusion. We’ll break this down into four pillars:
	1.	Meaningful Names – Use clear, descriptive names that reveal intent.
	2.	Small Functions – Functions should do one thing and do it well.
	3.	DRY (Don’t Repeat Yourself) – Avoid duplicating logic or knowledge.
	4.	Comments Only When Necessary – Prefer self-explanatory code over explanatory comments.
	
	

1. Meaningful Names

Prompt yourself:
	•	Does the name reveal what the variable, function, or class does?
	•	Is the name pronounceable and searchable?
	•	Is there consistency in naming patterns across the codebase?
	•	Could the name be misleading or too generic (e.g., data, temp, handle)?
	•	Are booleans phrased as questions (e.g., isActive, hasPermission)?
	
<example>

# Bad

```
def do_stuff(a, b):
    return a * b + 1
```

# Good
```
def discounted_price(price, tax_rate):
    return price * tax_rate + 1
```

Improvement: Names should describe behavior and domain, not just structure.

<example>


2. Small Functions

Prompt yourself:
	•	Does the function have a single responsibility?
	•	Can I describe what it does in one sentence?
	•	Is it < 15 lines long, ideally 3–5?
	•	Does the function do only one level of abstraction?
	•	Are side effects hidden inside long methods?

<example>

 Large Function (Anti-pattern)
 
 ```
 def register_user(request):
    # Extract user data
    name = request.get('name')
    email = request.get('email')
    password = request.get('password')

    # Validate data
    if not name or not email or not password:
        raise ValueError("Missing fields")

    if '@' not in email:
        raise ValueError("Invalid email")

    # Hash password
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Save to DB
    user = {
        "name": name,
        "email": email,
        "password": hashed_password
    }
    database.insert("users", user)

    # Send welcome email
    send_email(email, "Welcome!", f"Hi {name}, thanks for registering.")

    # Return success
    return {"status": "success"}
 ```


Problems:
	•	Does too many things: parsing, validation, hashing, persistence, emailing.
	•	Difficult to test or modify any part without risk.
	•	Not reusable or composable.
	
	
Refactored: Small, Focused Functions

```
def register_user(request):
    user_data = extract_user_data(request)
    validate_user_data(user_data)
    hashed_user = hash_password(user_data)
    save_user(hashed_user)
    send_welcome_email(user_data["email"], user_data["name"])
    return {"status": "success"}


def extract_user_data(request):
    return {
        "name": request.get('name'),
        "email": request.get('email'),
        "password": request.get('password'),
    }


def validate_user_data(data):
    if not data["name"] or not data["email"] or not data["password"]:
        raise ValueError("Missing fields")
    if '@' not in data["email"]:
        raise ValueError("Invalid email")


def hash_password(data):
    import hashlib
    hashed = hashlib.sha256(data["password"].encode()).hexdigest()
    return {**data, "password": hashed}


def save_user(user):
    database.insert("users", user)


def send_welcome_email(email, name):
    send_email(email, "Welcome!", f"Hi {name}, thanks for registering.")

```


<example>

3. DRY (Don’t Repeat Yourself)

Prompt yourself:
	•	Is the same logic repeated in multiple places?
	•	Is there an opportunity to extract a function or class?
	•	Are you copy-pasting code instead of abstracting it?
	•	Could a utility function, helper, or shared constant improve this?
	
	
<example>

# Bad
```
if user.is_admin and user.status == 'active':
    ...
```

# later in code:
```
if user.is_admin and user.status == 'active':
    ...
```

# Good
```
def is_active_admin(user):
    return user.is_admin and user.status == 'active'
```    

Improvement: Reduces bugs, centralizes changes, enhances reusability.

<example>

4. Comments Only When Necessary

Prompt yourself:
	•	Can I rename the function/variable to remove the need for a comment?
	•	Is this comment describing the why, not the what?
	•	Is the comment outdated or wrong?
	•	Am I using a comment to justify bad code?

<example>

# Bad

```
# Check if the user is an admin and is active
if user.is_admin and user.status == 'active':
    ...
```

# Good (self-explanatory, no comment needed)
```
if is_active_admin(user):
    ...
```

Acceptable comments:
	•	TODOs
	•	Warnings
	•	Complex algorithm explanations
	•	Legal/licensing reasons

<example>

Putting It All Together
<example>

Violating Clean Code Practices:
# Bad naming, large function, duplication, and unnecessary comment
```
def d(u, t):
    # check if user can access
    if u.is_admin and u.status == 'active':
        return True
    if u.is_admin and u.status == 'active':
        return True
    # access denied
    return False
```

Cleaned Version
```
def is_active_admin(user):
    return user.is_admin and user.status == 'active'

def can_user_access(user):
    return is_active_admin(user)
```

Why it’s better:
	•	Expressive names: can_user_access, is_active_admin
	•	Removed duplication
	•	Eliminated need for comments
	•	Readable in one glance
	
<example>

Clean Code Review Checklist
	•	Do function names describe their behavior accurately?
	•	Are functions small and do one thing?
	•	Is there duplication across files or methods?
	•	Are comments used only when needed, or can the code speak for itself?
"""


CODE_REVIEW_BEST_PRACTICES = """Code Review Best Practices are a set of guidelines and mental models that engineers follow when evaluating code submitted by their peers. The goal is to ensure that code is:
	•	Readable – Easy to understand and follow
	•	Maintainable – Easy to change, extend, or debug in the future
	•	Performant – Does not introduce unnecessary inefficiencies or regressions

Code reviews are not just for catching bugs — they are a shared quality gate for engineering culture, consistency, and collaboration.


Use these internal prompts during review to evaluate the code critically but constructively:
1. Readability

Ask yourself:
	•	Can I understand this code without asking the author?
	•	Are variable, function, and class names clear and descriptive?
	•	Is the code broken into logical blocks or functions?
	•	Are control flows (e.g., loops, conditionals, exits) easy to trace?
	•	Would a junior engineer or your future self grok this in a week?
	
<example>
1. Can I understand this code without asking the author?

Before: Poor context

```
def process(x):
    if x > 0:
        y = x * 3.14
        return y
```

After: Self-explanatory

```
def area(radius):
    if radius > 0:
        area = radius * 3.14
        return area
```
Why it’s better: Function and variable names convey purpose. No need to guess what x or y are.


2. Are variable, function, and class names clear and descriptive?

Before: Vague names

```
def d(u):
    for i in u:
        print(i)
```


After: Clear names
```
def display_usernames(usernames):
    for username in usernames:
        print(username)
```
Why it’s better: Descriptive naming makes the code intention obvious.


3. Is the code broken into logical blocks or functions?

Before: Monolithic function

```
def handle_order(order):
    # validate
    if not order['items']:
        raise ValueError("No items")
    # calculate total
    total = sum(item['price'] for item in order['items'])
    # print receipt
    print("Receipt:")
    for item in order['items']:
        print(f"{item['name']}: ${item['price']}")
    print(f"Total: ${total}")
```

After: Modular structure

```
def handle_order(order):
    validate_order(order)
    total = get_total(order)
    print_receipt(order, total)

def validate_order(order):
    if not order['items']:
        raise ValueError("No items")

def get_total(order):
    return sum(item['price'] for item in order['items'])

def print_receipt(order, total):
    print("Receipt:")
    for item in order['items']:
        print(f"{item['name']}: ${item['price']}")
    print(f"Total: ${total}")
```

Why it’s better: Clear separation of concerns makes the code more maintainable and testable.

4. Are control flows (e.g., loops, conditionals, exits) easy to trace?

Before: Nested, hard to follow

```
def check_access(user):
    if user:
        if user['role'] == 'admin':
            if user['active']:
                return True
    return False
```

After: Flattened and clear

```
def check_access(user):
    if not user:
        return False
    if user['role'] != 'admin':
        return False
    return user['active']
```

Why it’s better: Early exits and simpler conditionals make the logic much easier to follow.

5. Would a junior engineer or your future self grok this in a week?

Before: Clever but cryptic

```
def f(x): return x and not x % 2
```

After: Clear intent

```
def is_even(number):
    return number != 0 and number % 2 == 0
```
Why it’s better: Avoids unnecessary cleverness. Future-you (or a new teammate) will understand the logic instantly.

<example>

2. Maintainability

Ask yourself:
	•	Is the logic isolated into small testable units?
	•	Is there repeated code that can be abstracted?
	•	Are side effects clearly separated?
	•	Are dependencies injected or hardcoded?
	•	Does the code follow conventions or dev standards?

<example>

1. Is the logic isolated into small testable units?

Before: All logic in one large function

```
def process_order(order):
    if not order['items']:
        raise ValueError("Order has no items")

    total = 0
    for item in order['items']:
        total += item['price']
    
    print(f"Order total: {total}")
    send_email(order['customer_email'], f"Your total is {total}")
```

 After: Isolated units
 
 ```
 def process_order(order):
    validate_order(order)
    total = get_total(order['items'])
    print_total(total)
    notify_customer(order['customer_email'], total)

def validate_order(order):
    if not order['items']:
        raise ValueError("Order has no items")

def get_total(items):
    return sum(item['price'] for item in items)

def print_total(total):
    print(f"Order total: {total}")

def notify_customer(email, total):
    send_email(email, f"Your total is {total}")
 ```

Why it’s better: Each piece is independently testable, reusable, and easier to debug or extend.

2. Is there repeated code that can be abstracted?

Before: Duplicated logic

```
def send_welcome_email(user):
    subject = "Welcome"
    body = f"Hi {user['name']}, welcome!"
    email_service.send(user['email'], subject, body)

def send_password_reset_email(user):
    subject = "Reset Password"
    body = f"Hi {user['name']}, click here to reset."
    email_service.send(user['email'], subject, body)
```

After: Abstracted common logic

```
def send_email_to_user(user, subject, body_template):
    body = body_template.format(name=user['name'])
    email_service.send(user['email'], subject, body)

# Usage
send_email_to_user(user, "Welcome", "Hi {name}, welcome!")
send_email_to_user(user, "Reset Password", "Hi {name}, click here to reset.")
```

Why it’s better: DRY (Don’t Repeat Yourself). Centralized logic reduces maintenance burden.

3. Are side effects clearly separated?

Before: Mixing logic and side effects

```
def get_discount(order):
    if order['customer']['loyalty_level'] == 'gold':
        order['discount'] = 0.2
        logger.info("Gold discount applied")
    return order['total'] * (1 - order['discount'])
```

After: Separate computation and side effect

```
def get_discount_rate(customer):
    return 0.2 if customer['loyalty_level'] == 'gold' else 0.0

def apply_discount(order):
    rate = get_discount_rate(order['customer'])
    logger.info(f"{order['customer']['name']} discount rate: {rate}")
    return order['total'] * (1 - rate)
```
Why it’s better: Calculation is now pure; side effects like logging are cleanly separated and optional in tests.

4. Are dependencies injected or hardcoded?

Before - Anti-pattern: Hardcoded dependency

```
class OrderProcessor:
    def __init__(self):
        # Direct instantiation (tight coupling)
        self.payment_gateway = StripePaymentGateway(api_key="secret")

    def process(self, order):
        self.payment_gateway.charge(order.amount)
```

After - improved: Dependency Injection (Constructor-based)

```
class OrderProcessor:
    def __init__(self, payment_gateway):
        self.payment_gateway = payment_gateway

    def process(self, order):
        self.payment_gateway.charge(order.amount)

# Now you can inject any implementation
class StripePaymentGateway:
    def __init__(self, api_key):
        self.api_key = api_key

    def charge(self, amount):
        print(f"Charging ${amount} via Stripe")

class MockPaymentGateway:
    def charge(self, amount):
        print(f"[MOCK] Would charge ${amount}")

# Usage
real_processor = OrderProcessor(StripePaymentGateway(api_key="secret"))
real_processor.process(order={"amount": 100})

test_processor = OrderProcessor(MockPaymentGateway())
test_processor.process(order={"amount": 100})
```

Why this is better:
	•	Loosely coupled: OrderProcessor doesn’t care which gateway it uses.
	•	Testable: Easily swap in MockPaymentGateway during tests.
	•	Open for extension: Add new gateways (e.g., PayPal) without modifying OrderProcessor.

5. Does the code follow conventions or dev standards?

Before: Violates naming and style guides

```
def ProcessData(DATA):
    for i in DATA:
        print(i)
```

After: Follows naming and style conventions (e.g., PEP8 for Python)

```
def process_data(data):
    for item in data:
        print(item)
```
Why it’s better: Consistency with team or language standards improves comprehension and reduces onboarding time.

<example>

3. Performance Considerations

Ask yourself:
	•	Is the code using efficient data structures and algorithms?
	•	Are there redundant computations inside loops or queries?
	•	Could this logic become slow at scale (100k+ records, concurrent users)?
	•	Are we introducing any N+1 query patterns or unbounded loops?
	•	Is memory usage considered in long-lived processes?

<example>
1. Is the code using efficient data structures and algorithms?

Before: Inefficient search using a list

```
def is_user_blacklisted(user_id, blacklist: List[str]):
    return user_id in blacklist  # blacklist is a list
```

After: Use a set for O(1) lookup

```
def is_user_blacklisted(user_id, blacklist_set):
    return user_id in blacklist_set  # set lookup is O(1)
```

Why it’s better: For large lists, switching to a set drastically improves performance.

2. Are there redundant computations inside loops or queries?

Before: Expensive operation repeated in loop

```
for user in users:
    user_data = fetch_user_data_from_db(user.id)
    process(user_data)
```

After: Compute once outside loop

```
user_ids = [user.id for user in users]
all_user_data = fetch_bulk_user_data(user_ids)  # batch fetch
for user_data in all_user_data:
    process(user_data)
```

Why it’s better: Avoids N repeated DB calls by batching.

3. Could this logic become slow at scale (100k+ records, concurrent users)?

Before: O(n²) nested loop for duplicate detection

```
def has_duplicates(items):
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                return True
    return False
```

After: Use a set for linear time detection

```
def has_duplicates(items):
    seen = set()
    for item in items:
        if item in seen:
            return True
        seen.add(item)
    return False
```

Why it’s better: Reduces complexity from O(n²) to O(n) — critical at large scale.


4. Are we introducing any N+1 query patterns or unbounded loops?

Before: N+1 Query Problem (typical ORM anti-pattern)

```
# Get posts and fetch each author's name separately
posts = Post.query.all()
for post in posts:
    print(post.author.name)  # Triggers separate query for each author
```

After: Use JOIN or ORM eager loading

```
# Use joinedload or prefetch to batch load authors
posts = Post.query.options(joinedload(Post.author)).all()
for post in posts:
    print(post.author.name)
```

5. Is memory usage considered in long-lived processes?

Before: Accumulating unnecessary data in memory

```
# In a background worker
all_logs = []
for log in stream_logs():
    all_logs.append(log)
    if "ERROR" in log:
        alert_admin(log)
```

After: Stream and process on-the-fly

```
for log in stream_logs():
    if "ERROR" in log:
        alert_admin(log)
```

Why it’s better: Keeps memory flat regardless of input size. Avoids memory leaks in daemons, workers, or services.

<example>"""


REFACTORING_BEST_PRACTICES = """Refactoring is the process of improving the structure, readability, and maintainability of code without changing its external behavior. Good refactoring eliminates “code smells”, improves modularity, and enables easier testing and enhancement.

1. Code Smells Identification
Are there any code smells like long methods, large classes, repeated logic, or feature envy?

<example>
Before (Long Method)

```
def register_user(data):
    if not data.get("email") or "@" not in data["email"]:
        raise ValueError("Invalid email")
    if len(data.get("password", "")) < 8:
        raise ValueError("Password too short")
    user = User(data["email"], data["password"])
    db.save(user)
    send_email(data["email"], "Welcome!")
```

After (Extract Methods)

```
def register_user(data):
    validate_input(data)
    user = create_user(data)
    send_welcome_email(user)

def validate_input(data):
    if not data.get("email") or "@" not in data["email"]:
        raise ValueError("Invalid email")
    if len(data.get("password", "")) < 8:
        raise ValueError("Password too short")

def create_user(data):
    user = User(data["email"], data["password"])
    db.save(user)
    return user

def send_welcome_email(user):
    send_email(user.email, "Welcome!")
```

 Why this is better:
	•	Logic is grouped and testable.
	•	Avoids a “long method” code smell.
	•	Naming makes intention explicit.

<example>

2. Design Pattern Implementation
Is there repeated or brittle logic that could be improved with a design pattern?

<example>

Before: Switch-based logic (violates Open/Closed)

```
def calculate_price(order):
    if order.type == "digital":
        return order.base_price
    elif order.type == "physical":
        return order.base_price + order.shipping_cost
    elif order.type == "subscription":
        return order.base_price * 12
```

After: Use Strategy Pattern

```
class PricingStrategy:
    def calculate(self, order): raise NotImplementedError

class DigitalProduct(PricingStrategy):
    def calculate(self, order): return order.base_price

class PhysicalProduct(PricingStrategy):
    def calculate(self, order): return order.base_price + order.shipping_cost

class SubscriptionProduct(PricingStrategy):
    def calculate(self, order): return order.base_price * 12

# Usage
strategy = get_strategy(order.type)
price = strategy.calculate(order)
```

Why this is better:
	•	Open to extension (new product types).
	•	Closed to modification (don’t touch existing logic).
	•	Easier to test per class.

<example>

3. Legacy Code Improvement

Is the legacy code tightly coupled, untested, or full of side effects?


<example>

Before: Legacy monolith with implicit behavior

```
def calculate_final_score(user):
    if user.is_premium:
        score = (user.points * 2) + 100
        logging.info("Premium user")
    else:
        score = user.points
    update_score_in_legacy_db(user.id, score)
    return score
```

After: Decouple side effects and logic

```
class ScoreCalculator:
    def calculate(self, user):
        if user.is_premium:
            return (user.points * 2) + 100
        return user.points

class ScoreUpdater:
    def __init__(self, db):
        self.db = db

    def update(self, user, score):
        self.db.update(user.id, score)

# Usage
score = ScoreCalculator().calculate(user)
ScoreUpdater(legacy_db).update(user, score)
```

Why this is better:
	•	Pure logic is testable.
	•	Side effects (DB writes) are contained.
	•	Legacy system is gradually isolated for easier replacement.

<example>"""