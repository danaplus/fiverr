import json
from pathlib import Path
from typing import Union, List

import openai
from data_classifier import PolicyChecker, logger, Config, config

class ImagePolicyChecker(PolicyChecker):
    """
    Custom PolicyChecker that inherits all functionality from the base class.
    Ready to be extended with custom features as needed.
    """
    def __init__(self, config: Config):
        # Initialize the parent class with all its original functionality
        super().__init__(config)

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
                name="Image Rule Checker",
                instructions="Analyze uploaded files and images. Check if images violate rules stated in the text file.",
                model="gpt-4-turbo",
                tools=[{"type": "file_search"}]

            )
            self.assistant_id = assistant.id
            logger.info(f"Assistant created with ID: {self.assistant_id}")

        except openai.OpenAIError as e:
            logger.error(f"Error setting up assistant: {e}")
            raise
    def check_policy_violation(self, image, image_id: Union[int]) -> None:
        try:
            thread = openai.beta.threads.create()
            thread_id = thread.id
            prompt = f"""
             Check if the image violates any rules stated in the document.
             Please also determine if there is a clear violation, potential violation or no violation.
             please use the following format:
             "The decision: violation/ no violation"
             "The violated rules taken from text file: THE RULES HERE."
             "Image url: URL"
             
             """

            message = openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=[{"type": "text", "text": prompt},{"type": "image_url", "image_url": {"url": image}}],
                attachments=[
                    {"file_id": self.file_id, "tools": [{"type": "file_search"}]},
                    #{"file_id": image.id}
                ]
            )

            # Create and monitor run
            run = openai.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            if self._wait_for_run_completion(thread_id, run.id):
                response = self._get_assistant_response(thread_id)
                if response:
                    self.results[image_id] = response
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
                for image, response in self.results.items():
                    f.write(f"Image:\r{image}\n\n")
                    f.write(f"Response:\n{response}\n")
                    f.write("-" * 80 + "\n\n")
            logger.info(f"Results saved to {output_file}")
        except IOError as e:
            logger.error(f"Error saving results: {e}")


def main():

    # Initialize paths
    base_path = Path("home_assign/home_assign")
    images_path = base_path / "images"
    rules_file = base_path / "tos.txt"
    output_file = Path("image_results_dict.txt")



    # Initialize and run policy checker
    checker = ImagePolicyChecker(config)
    checker.setup_assistant(rules_file)
    image_id = 0


    image_urls = ["https://s3.us-east-1.amazonaws.com/www.danaeder.com/images/Graphic_Violence.jpg"
    ,"https://s3.us-east-1.amazonaws.com/www.danaeder.com/images/Huskiesatrest.jpg"
    ,"https://s3.us-east-1.amazonaws.com/www.danaeder.com/images/Mona_Lisa,_by_Leonardo_da_Vinci,_from_C2RMF_retouched.jpg"
    ,"https://s3.us-east-1.amazonaws.com/www.danaeder.com/images/Panorámica_Otoño_Alcázar_de_Segovia.jpg"
    ,r"https://s3.us-east-1.amazonaws.com/www.danaeder.com/images/images (2).jpg"]

    for image in image_urls:
        image_id += 1
        checker.check_policy_violation(image, image_id)

    checker.save_results(output_file)


if __name__ == "__main__":
    main()