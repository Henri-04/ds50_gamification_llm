"""Tests d'Agent 1 — extraction et reconstruction de l'ontologie (sans LLM)."""

from src.agent.agent1 import (
    extract_structure,
    apply_filter,
    fallback_keep,
    ns_of,
    derive_prefix,
)


def test_ns_of_handles_hash_and_slash():
    assert ns_of("http://x.org/tbox#Foo") == "http://x.org/tbox#"
    assert ns_of("http://x.org/path/Foo") == "http://x.org/path/"


def test_derive_prefix_known_and_pedago():
    assert derive_prefix("http://www.w3.org/2002/07/owl#") == "owl"
    assert derive_prefix("http://www.hds.utc.fr/tgc/tbox#") == "tgc"


def test_extract_structure_non_empty():
    s = extract_structure()
    assert s["classes"]
    assert s["object_properties"]
    names = {c["name"] for c in s["classes"]}
    # Classes socle attendues dans l'ontologie TGC.
    assert {"Teacher", "Learner", "GamifiedResource"} <= names


def test_apply_filter_keeps_anchors():
    s = extract_structure()
    keep = fallback_keep(s)
    result = apply_filter(s, keep)
    kept_names = {c["name"] for c in result["classes"]}
    # Les classes d'ancrage sont toujours conservées, même via le repli.
    assert "Teacher" in kept_names
    assert "GamifiedResource" in kept_names


def test_apply_filter_preserves_hierarchy_integrity():
    """Tout parent référencé dans la sortie doit lui-même être présent."""
    s = extract_structure()
    keep = fallback_keep(s)
    result = apply_filter(s, keep)
    kept_uris = {c["uri"] for c in result["classes"]}
    for c in result["classes"]:
        for parent in c.get("parents", []):
            assert parent in kept_uris
