from pydantic import BaseModel

from llmops_training.news_reader.generation import generate_object, generate_text


def test_generate_text():
    resp = generate_text(prompt="Say 'Good morning!' in Dutch")
    assert "goedemorgen!" in resp.strip().lower()


def test_generate_object() -> None:
    class User(BaseModel):
        name: str
        age: int

    resp = generate_object(
        prompt="Extract Jason is 25 years old.",
        response_model=User,
    )

    assert isinstance(resp, User)
    assert resp.name == "Jason"
    assert resp.age == 25
