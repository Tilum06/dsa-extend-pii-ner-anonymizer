from src.regex_detector import detect_by_regex
from src.context_detector import detect_by_context
from src.merger import merge_entities
from src.anonymizer import anonymize_text, build_token_entity_dict, build_token_entity_list


def test_anonymize_text_legacy():
    """Test anonymizing text with legacy dict input."""
    text = "I'm Tran Dinh Y"
    entities = {"I'm": "O", "Tran": "NAME", "Dinh": "NAME", "Y": "NAME"}
    result = anonymize_text(text, entities)
    print("=== Legacy dict mode ===")
    print(f"Input:  {text}")
    print(f"Result: {result}")
    print()


def test_full_pipeline():
    """Test the full detection → merge → anonymize pipeline."""
    test_texts = [
        "My name is Tran Dinh Y, email: trandinhy@gmail.com, phone: +84 912 345 678.",
        "Contact John Smith at john.smith@example.com or visit https://example.com/profile.",
        "I'm Jane Doe, my username is jane_doe123. I live at 123 Main Street.",
    ]

    for text in test_texts:
        print(f"{'='*70}")
        print(f"Input: {text}")
        print(f"{'='*70}")

        # Step 1: Detect entities from both detectors
        regex_entities = detect_by_regex(text)
        context_entities = detect_by_context(text)

        print(f"\n  Regex entities:   {regex_entities}")
        print(f"  Context entities: {context_entities}")

        # Step 2: Merge with priority-based overlap resolution
        merged = merge_entities(regex_entities, context_entities)
        print(f"  Merged entities:  {merged}")

        # Step 3: Build token → entity dict
        token_dict = build_token_entity_dict(text, merged)
        print(f"\n  Token dict: {token_dict}")

        # Step 4: Ordered token-entity pairs
        token_list = build_token_entity_list(text, merged)
        print(f"  Token list: {token_list}")

        # Step 5: Anonymize
        result = anonymize_text(text, merged)
        print(f"\n  Anonymized: {result}")
        print()


if __name__ == "__main__":
    test_anonymize_text_legacy()
    test_full_pipeline()