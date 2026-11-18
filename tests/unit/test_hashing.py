from dataclasses import dataclass

import pytest

from victoriya_photo.storage.hashing import (
    FileCollisionError, copy_file_no_overwrite, sha256_file, unique_by_sha256,
)


def test_copy_keeps_source_hash_and_never_overwrites(tmp_path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "output" / "copy.jpg"
    source.write_bytes(b"original-photo-bytes")
    source_hash_before = sha256_file(source)

    assert copy_file_no_overwrite(source, destination) is True
    assert copy_file_no_overwrite(source, destination) is False
    assert sha256_file(source) == source_hash_before
    assert destination.read_bytes() == source.read_bytes()


def test_different_existing_file_is_not_overwritten(tmp_path) -> None:
    source = tmp_path / "source.jpg"
    destination = tmp_path / "output.jpg"
    source.write_bytes(b"new")
    destination.write_bytes(b"keep-this")
    with pytest.raises(FileCollisionError):
        copy_file_no_overwrite(source, destination)
    assert destination.read_bytes() == b"keep-this"


def test_exact_duplicates_are_detected_not_similar_hashes() -> None:
    @dataclass
    class Item:
        name: str
        sha256: str

    items = [
        Item("first", "a" * 64),
        Item("duplicate", "a" * 64),
        Item("different", "b" * 64),
    ]
    assert [item.name for item in unique_by_sha256(items)] == ["first", "different"]
