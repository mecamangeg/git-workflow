"""Tests for Vercel integration"""
import pytest
from service.vercel import VercelIntegration


def test_vercel_integration_initialization():
    """Test VercelIntegration initializes"""
    vercel = VercelIntegration()
    assert vercel is not None


def test_is_configured_without_token():
    """Test is_configured returns False without token"""
    vercel = VercelIntegration(api_token=None)
    assert not vercel.is_configured()


def test_is_configured_with_token():
    """Test is_configured returns True with token"""
    vercel = VercelIntegration(api_token="test_token_123")
    assert vercel.is_configured()


def test_get_recent_deployments_without_token():
    """Test get_recent_deployments returns empty list without token"""
    vercel = VercelIntegration(api_token=None)
    deployments = vercel.get_recent_deployments()
    assert deployments == []


def test_check_deployment_status_without_token():
    """Test check_deployment_status returns None without token"""
    vercel = VercelIntegration(api_token=None)
    status = vercel.check_deployment_status("test_id")
    assert status is None


def test_get_deployment_url_without_deployments():
    """Test get_deployment_url returns None when no deployments"""
    vercel = VercelIntegration(api_token=None)
    url = vercel.get_deployment_url("test-branch")
    assert url is None


def test_test_connection_without_token():
    """Test test_connection fails without token"""
    vercel = VercelIntegration(api_token=None)
    result = vercel.test_connection()
    assert result is False


# Note: Real API tests would require valid Vercel token
# and should be run separately or mocked
