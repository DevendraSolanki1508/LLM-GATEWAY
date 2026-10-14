import random
from locust import HttpUser, task, between

# Each pair: an original question and a reworded version of it.
QUESTIONS = [
    ("What is the capital of Germany?", "Tell me the capital city of Germany"),
    ("What is 15 times 12?", "Calculate 15 multiplied by 12"),
    ("Who painted the Mona Lisa?", "Name the painter of the Mona Lisa"),
    ("What is the boiling point of water in Celsius?", "At what Celsius temperature does water boil?"),
    ("How many continents are there?", "What is the number of continents?"),
    ("What is the largest planet in our solar system?", "Which planet is the biggest in the solar system?"),
    ("Who discovered penicillin?", "Name the discoverer of penicillin"),
    ("What is the chemical symbol for gold?", "Which symbol represents gold in chemistry?"),
]


class GatewayUser(HttpUser):
    wait_time = between(0.5, 2)

    @task
    def ask(self):
        original, reworded = random.choice(QUESTIONS)
        # Original twice as likely as reworded: a repeat-heavy workload
        prompt = random.choice([original, original, reworded])
        self.client.post("/chat", json={"prompt": prompt}, name="/chat")
