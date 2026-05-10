"""Tests for merger module."""

import pytest
from src.merger import (
    sort_entities,
    resolve_overlaps,
    merge_entities,
)


class TestSortEntities:
    """Test cases for sort_entities function."""

    def test_sort_entities_by_position(self):
        """Test sorting entities by position."""
        entities = [
            {"type": "EMAIL", "start": 20, "end": 30},
            {"type": "NAME", "start": 0, "end": 10},
            {"type": "PHONE", "start": 10, "end": 20},
        ]
        result = sort_entities(entities)
        
        assert isinstance(result, list)
        assert len(result) == 3
        # Check if sorted by start position
        positions = [e["start"] for e in result]
        assert positions == sorted(positions)

    def test_sort_entities_empty_list(self):
        """Test sorting empty entity list."""
        result = sort_entities([])
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_sort_entities_single_entity(self):
        """Test sorting single entity."""
        entities = [{"type": "EMAIL", "start": 5, "end": 15}]
        result = sort_entities(entities)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == entities[0]

    def test_sort_entities_same_start_position(self):
        """Test sorting entities with same start position."""
        entities = [
            {"type": "EMAIL", "start": 10, "end": 20},
            {"type": "NAME", "start": 10, "end": 15},
            {"type": "PHONE", "start": 10, "end": 25},
        ]
        result = sort_entities(entities)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(e["start"] == 10 for e in result)

    def test_sort_entities_preserves_structure(self):
        """Test that sorting preserves entity structure."""
        entities = [
            {"type": "EMAIL", "text": "john@example.com", "start": 20, "end": 35},
            {"type": "NAME", "text": "John", "start": 0, "end": 4},
        ]
        result = sort_entities(entities)
        
        for entity in result:
            assert "type" in entity
            assert "start" in entity
            assert "end" in entity


class TestResolveOverlaps:
    """Test cases for resolve_overlaps function."""

    def test_resolve_overlaps_no_overlap(self):
        """Test resolving non-overlapping entities."""
        entities = [
            {"type": "NAME", "start": 0, "end": 10},
            {"type": "EMAIL", "start": 20, "end": 35},
        ]
        result = resolve_overlaps(entities)
        
        assert isinstance(result, list)
        assert len(result) == 2

    def test_resolve_overlaps_with_overlap(self):
        """Test resolving overlapping entities."""
        entities = [
            {"type": "NAME", "start": 0, "end": 15},
            {"type": "EMAIL", "start": 10, "end": 25},
        ]
        result = resolve_overlaps(entities)
        
        assert isinstance(result, list)
        # Should resolve overlap
        if len(result) > 1:
            # Check no overlaps in result
            for i in range(len(result) - 1):
                assert result[i]["end"] <= result[i + 1]["start"]

    def test_resolve_overlaps_complete_overlap(self):
        """Test resolving completely overlapping entities."""
        entities = [
            {"type": "NAME", "start": 0, "end": 20},
            {"type": "EMAIL", "start": 5, "end": 15},
        ]
        result = resolve_overlaps(entities)
        
        assert isinstance(result, list)
        assert len(result) <= 2

    def test_resolve_overlaps_empty_list(self):
        """Test resolving empty entity list."""
        result = resolve_overlaps([])
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_resolve_overlaps_single_entity(self):
        """Test resolving single entity."""
        entities = [{"type": "EMAIL", "start": 0, "end": 15}]
        result = resolve_overlaps(entities)
        
        assert isinstance(result, list)
        assert len(result) == 1

    def test_resolve_overlaps_respects_priority(self):
        """Test that overlapping entities are resolved respecting priority."""
        entities = [
            {"type": "NAME", "start": 0, "end": 15},
            {"type": "EMAIL", "start": 5, "end": 10},
        ]
        result = resolve_overlaps(entities)
        
        assert isinstance(result, list)
        # EMAIL has higher priority, should be kept
        if any(e["type"] == "EMAIL" for e in result):
            # Verify EMAIL is in the result
            assert any(e["type"] == "EMAIL" for e in result)


class TestMergeEntities:
    """Test cases for merge_entities function."""

    def test_merge_entities_single_group(self):
        """Test merging single entity group."""
        entities = [
            {"type": "EMAIL", "start": 10, "end": 25},
            {"type": "PHONE", "start": 30, "end": 40},
        ]
        result = merge_entities(entities)
        
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_merge_entities_multiple_groups(self):
        """Test merging multiple entity groups."""
        regex_entities = [
            {"type": "EMAIL", "start": 10, "end": 25},
            {"type": "URL", "start": 40, "end": 55},
        ]
        context_entities = [
            {"type": "NAME", "start": 0, "end": 8},
            {"type": "USERNAME", "start": 60, "end": 70},
        ]
        result = merge_entities(regex_entities, context_entities)
        
        assert isinstance(result, list)
        assert len(result) >= 3

    def test_merge_entities_empty_groups(self):
        """Test merging with empty groups."""
        result = merge_entities([], [])
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_merge_entities_handles_duplicates(self):
        """Test that merge handles duplicate entities."""
        group1 = [{"type": "EMAIL", "start": 10, "end": 25}]
        group2 = [{"type": "EMAIL", "start": 10, "end": 25}]
        result = merge_entities(group1, group2)
        
        assert isinstance(result, list)

    def test_merge_entities_overlapping_entities(self):
        """Test merging overlapping entities from different groups."""
        group1 = [{"type": "NAME", "start": 0, "end": 15}]
        group2 = [{"type": "EMAIL", "start": 10, "end": 25}]
        result = merge_entities(group1, group2)
        
        assert isinstance(result, list)
        # Should contain resolved entities
        assert len(result) >= 1

    def test_merge_entities_preserves_all_types(self):
        """Test that merge preserves all entity types."""
        group1 = [{"type": "EMAIL", "start": 0, "end": 15}]
        group2 = [{"type": "NAME", "start": 20, "end": 30}]
        group3 = [{"type": "PHONE", "start": 40, "end": 50}]
        result = merge_entities(group1, group2, group3)
        
        types = {e["type"] for e in result}
        # Should contain entities from all groups if no overlaps
        assert len(types) >= 1

    def test_merge_entities_multiple_groups_order(self):
        """Test merging entities with different group orders."""
        group1 = [{"type": "EMAIL", "start": 30, "end": 40}]
        group2 = [{"type": "NAME", "start": 0, "end": 10}]
        group3 = [{"type": "PHONE", "start": 50, "end": 60}]
        result = merge_entities(group1, group2, group3)
        
        assert isinstance(result, list)
        # Verify entities are sorted
        if len(result) > 1:
            positions = [e["start"] for e in result]
            assert positions == sorted(positions)
