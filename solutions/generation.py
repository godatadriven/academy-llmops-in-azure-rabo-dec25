import os

import dotenv
import instructor
from instructor.client import Instructor
from openai import AzureOpenAI
from pydantic import BaseModel

dotenv.load_dotenv()


def get_azure_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )


def generate_text(prompt: str, model_name: str = "o3-mini", **kwargs) -> str:
    """Generates text from a prompt using the specified model."""
    azure_client = get_azure_client()

    generation_config = {
        "temperature": 1,
        "max_completion_tokens": 4096,
    }
    generation_config.update(kwargs)
    response = azure_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        **generation_config,
    )
    return response.choices[0].message.content


def get_instructor_client() -> Instructor:
    """Returns an Instructor client for the specified model.

    This client can be used to generate structured Pydantic objects from prompts.
    See: https://python.useinstructor.com/
    """

    azure_client = get_azure_client()
    client = instructor.from_openai(client=azure_client, mode=instructor.Mode.TOOLS)
    return client


def generate_object(
    prompt: str, response_model: BaseModel, model_name: str = "o3-mini", **kwargs
) -> BaseModel:
    """Uses the Instructor client to generate a structured Pydantic object from a prompt."""
    client = get_instructor_client()

    generation_config = {
        "temperature": 1,
        "max_completion_tokens": 4096,
    }
    generation_config.update(kwargs)
    return client.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_model=response_model,
        **generation_config,
    )


async def generate_object_async(
    prompt: str,
    response_model: BaseModel,
    model_name: str = "o3-mini",
    **kwargs,
) -> BaseModel:
    """Asynchronous version of generate_object function.

    For more info, see: https://python.useinstructor.com/blog/2023/11/13/learn-async/
    """
    client = get_instructor_client()
    generation_config = {
        "temperature": 1,
        "max_completion_tokens": 4096,
    }
    generation_config.update(kwargs)
    return await client.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_model=response_model,
        **generation_config,
    )
