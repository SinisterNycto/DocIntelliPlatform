from app.rag.citations import (
    answer_was_not_found,
    append_sources,
    citation_label,
    citation_labels,
    history_without_current_question,
    message_text,
)


class Doc:
    def __init__(self, metadata):
        self.metadata = metadata


def test_history_drops_the_question_just_asked():
    history = [
        {"role": "user", "content": "What is clustering?"},
        {"role": "assistant", "content": "It pools workers."},
        {"role": "user", "content": "And the default?"},
    ]
    prior = history_without_current_question(history, "And the default?")
    assert [msg["content"] for msg in prior] == ["What is clustering?", "It pools workers."]


def test_history_kept_when_last_turn_is_not_the_question():
    history = [{"role": "assistant", "content": "Earlier answer"}]
    assert history_without_current_question(history, "New question") == history


def test_citation_uses_retrieved_metadata_not_model_urls():
    docs = [
        Doc({"source": "https://example.com/docs", "document_id": "abc"}),
        Doc({"source": "guide.pdf", "page": 3.0}),
        Doc({"source": "guide.pdf", "page": 3}),
    ]
    assert citation_labels(docs) == ["https://example.com/docs", "guide.pdf (page 3)"]
    assert citation_label({"source": "notes.pdf", "page": 1}) == "notes.pdf (page 1)"


def test_message_text_reads_string_and_block_content():
    class Msg:
        content = [{"type": "text", "text": "  standalone question  "}]

    assert message_text(Msg()) == "standalone question"
    assert message_text(type("M", (), {"content": "already standalone"})()) == "already standalone"


def test_not_found_answers_do_not_keep_sources():
    assert answer_was_not_found("The answer to this question was not found in the ingested documentation.")
    assert append_sources("Workers share the server.", ["https://example.com/docs"]).endswith(
        "* Source: [https://example.com/docs](https://example.com/docs)\n"
    )
