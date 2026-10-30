from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "web/arkadia_console/src/pages/ArkanaPage.tsx"
MARKDOWN = ROOT / "web/arkadia_console/src/components/arkana/MarkdownViewer.tsx"


def test_arkana_cards_select_modes_without_sending_their_copy():
    source = PAGE.read_text(encoding="utf-8")
    assert 'onClick={() => activateMode(mode.id)}' in source
    assert 'onClick={() => void send(item.prompt)}' not in source
    assert 'aria-pressed={activeMode === mode.id}' in source


def test_research_queries_the_existing_knowledge_os_contract():
    source = PAGE.read_text(encoding="utf-8")
    assert 'apiRequest<unknown>(endpoints.knowledgeSearch' in source
    assert 'modes: RESEARCH_SEARCH_MODES' in source
    assert 'isKnowledgeSearchData(payload)' in source
    assert 'top_k: 12' in source
    assert 'No research synthesis was generated.' in source


def test_markdown_is_rendered_in_the_main_conversation_canvas():
    source = PAGE.read_text(encoding="utf-8")
    renderer = MARKDOWN.read_text(encoding="utf-8")
    assert '<MarkdownViewer content={turn.content}' in source
    assert 'data-testid="arkana-conversation-canvas"' in source
    assert 'data-testid="arkana-markdown"' in renderer
    assert 'href.startsWith("https://")' in renderer
