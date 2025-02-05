import json
import os
import openai
import time
from pathlib import Path
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
import logging
import colorama
from colorama import Fore, Style

# Initialize colorama for Windows support
colorama.init()


# Create a custom formatter with white color
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Set white color for the message
        return f"{Fore.WHITE}{super().format(record)}{Style.RESET_ALL}"


# Configure logging with the custom formatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with custom formatter
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Remove any existing handlers and add our custom handler
logger.handlers = []
logger.addHandler(console_handler)


@dataclass
class Config:
    """Configuration settings for the policy checker."""
    api_key: str
    model_name: str = "gpt-4o-mini"
    poll_interval: int = 2
    encoding: str = "utf-8"


# Configuration
config = Config(
    api_key=os.getenv('OPEN_API_KEY'))


class PolicyChecker:
    def __init__(self, config: Config):
        """Initialize the PolicyChecker with configuration settings."""
        self.config = config
        openai.api_key = config.api_key
        openai.log = "debug"
        self.results: Dict[int, str] = {}
        self.file_id: Optional[str] = None
        self.assistant_id: Optional[str] = None

    def setup_assistant(self, rules_file: Path) -> None:
        """Set up the OpenAI assistant with the rules file."""
        try:
            # Upload rules file
            with open(rules_file, "rb") as f:
                file = openai.files.create(
                    file=f,
                    purpose="assistants"
                )
            self.file_id = file.id
            logger.info(f"File uploaded with ID: {self.file_id}")

            # Create assistant
            assistant = openai.beta.assistants.create(
                name="FileAnalyzer",
                instructions="You will analyze and answer questions about uploaded files.",
                model=self.config.model_name,
                tools=[{"type": "file_search"}]
            )
            self.assistant_id = assistant.id
            logger.info(f"Assistant created with ID: {self.assistant_id}")

        except openai.OpenAIError as e:
            logger.error(f"Error setting up assistant: {e}")
            raise

    def _wait_for_run_completion(self, thread_id: str, run_id: str) -> bool:
        """Wait for the assistant's run to complete."""
        while True:
            try:
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                status = run_status.status
                logger.debug(f"Run status: {status}")

                if status == "completed":
                    logger.info("Run completed successfully")
                    return True
                if status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Run ended with status: {status}")
                    return False

                time.sleep(self.config.poll_interval)

            except openai.OpenAIError as e:
                logger.error(f"Error checking run status: {e}")
                return False

    def _get_assistant_response(self, thread_id: str) -> Optional[str]:
        """Retrieve the assistant's response from the thread."""
        try:
            messages = openai.beta.threads.messages.list(thread_id=thread_id)
            for msg in reversed(messages.data):
                if msg.role == "assistant":
                    return msg.content[0].text.value
            return None

        except openai.OpenAIError as e:
            logger.error(f"Error retrieving assistant response: {e}")
            return None

    def check_policy_violation(self, conversation: Union[List, str], conv_id: Union[int]) -> None:
        """Check a conversation for policy violations."""
        if not self.assistant_id or not self.file_id:
            raise ValueError("Assistant not properly initialized")

        # Convert list to string if necessary
        conversation_str = json.dumps(conversation) if isinstance(conversation, list) else conversation


        prompt = f"""
                I have a Terms of Service (TOS) document (tos.txt) attached. I need to analyze chat logs to determine if they violate the TOS.

                For the chat provided and the value of X = {conv_id}, do the following:
                
                Identify if there is a violation based on the TOS.
                If a violation exists, label it as: "Chain X (Violation Chain):" followed by a clear explanation of the breach.
                If no violation exists, label it as: "Chain X (Non Violation Chain):" followed by a brief statement confirming compliance with the TOS.
                separate label from reason with \n
                Ensure the response is concise and directly tied to the TOS.
                please don't add any more data then i requested, no header and no footer.
                Chat: {conversation_str}
                """

        try:
            # Create thread
            thread = openai.beta.threads.create()
            thread_id = thread.id

            # Add message to thread
            openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt,
                attachments=[{
                    "file_id": self.file_id,
                    "tools": [{"type": "file_search"}]
                }]
            )

            # Create and monitor run
            run = openai.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            if self._wait_for_run_completion(thread_id, run.id):
                response = self._get_assistant_response(thread_id)
                if response:
                    # Use the string representation as the key
                    self.results[conv_id] = response
                    logger.info(f"Policy check completed for conversation")
                else:
                    logger.warning("No response received from assistant")
            else:
                logger.error("Run failed to complete successfully")

        except openai.OpenAIError as e:
            logger.error(f"Error during policy check: {e}")

    def save_results(self, output_file: Path) -> None:
        """Save results to a file."""
        try:
            with open(output_file, 'w', encoding=self.config.encoding) as f:
                f.write("Comments (comments.txt):\n\n")
                for conversation, response in self.results.items():
                    f.write(f"{response}\n\n")

            logger.info(f"Results saved to {output_file}")
        except IOError as e:
            logger.error(f"Error saving results: {e}")


def main():
    # Initialize paths
    base_path = Path("home_assign/home_assign")
    chat_file = base_path / "chat_chains.json"
    rules_file = base_path / "tos.txt"
    output_file = Path("results_dict.txt")

    # Load conversations
    try:
        with open(chat_file, "r", encoding="utf-8") as f:
            conversations = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error loading conversations: {e}")
        return
    except IOError as e:
        logger.error(f"Error reading chat file: {e}")
        return

    # Initialize and run policy checker
    checker = PolicyChecker(config)
    checker.setup_assistant(rules_file)
    conv_id = 0

    for conversation in conversations:
        conv_id += 1
        checker.check_policy_violation(conversation, conv_id)

    checker.save_results(output_file)


if __name__ == "__main__":
    main()
