"""Tests for violation detector"""
import pytest
from service.detector import ViolationDetector


def test_get_current_branch(temp_git_repo, mock_config_manager):
    """Test getting current branch name"""
    detector = ViolationDetector(mock_config_manager)

    branch = detector.get_current_branch(temp_git_repo)

    assert branch in ["main", "master"]


def test_get_current_branch_feature(temp_git_repo, mock_config_manager):
    """Test getting current branch on feature branch"""
    import subprocess

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "claude/test-feature-123"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True
    )

    detector = ViolationDetector(mock_config_manager)
    branch = detector.get_current_branch(temp_git_repo)

    assert branch == "claude/test-feature-123"


def test_has_uncommitted_changes(temp_git_repo, mock_config_manager):
    """Test detection of uncommitted changes"""
    detector = ViolationDetector(mock_config_manager)

    # Initially no changes
    assert not detector.has_uncommitted_changes(temp_git_repo)

    # Add uncommitted file
    (temp_git_repo / "new_file.txt").write_text("test content")

    # Should detect changes
    assert detector.has_uncommitted_changes(temp_git_repo)


def test_get_merged_branches(temp_git_repo, mock_config_manager):
    """Test getting merged branches"""
    import subprocess

    detector = ViolationDetector(mock_config_manager)

    # Create and merge a feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature-test"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True
    )

    (temp_git_repo / "feature.txt").write_text("feature")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True
    )

    subprocess.run(
        ["git", "checkout", "main"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "merge", "feature-test", "--no-edit"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True
    )

    merged = detector.get_merged_branches(temp_git_repo)

    assert "feature-test" in merged
    assert "main" not in merged
    assert "master" not in merged


def test_branch_name_validation(mock_config_manager):
    """Test branch naming pattern validation"""
    detector = ViolationDetector(mock_config_manager)

    # Valid branch names
    assert detector.is_branch_name_valid("claude/feature-name-011CV4zUPzgSkobBUdcow2EN")
    assert detector.is_branch_name_valid("claude/fix-bug-123abc456def789ghi012jkl")

    # Protected branches always valid
    assert detector.is_branch_name_valid("main")
    assert detector.is_branch_name_valid("master")

    # Invalid branch names
    assert not detector.is_branch_name_valid("feature/test")
    assert not detector.is_branch_name_valid("random-branch")
    assert not detector.is_branch_name_valid("claude/Feature-Name-123")
