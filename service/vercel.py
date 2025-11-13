"""
Git Workflow Guardian - Vercel Integration
Detects PR merges and deployment status
"""
import os
import requests
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class VercelIntegration:
    """Integration with Vercel for deployment notifications"""

    def __init__(self, api_token: Optional[str] = None, team_id: Optional[str] = None):
        self.api_token = api_token or os.getenv('VERCEL_API_TOKEN')
        self.team_id = team_id or os.getenv('VERCEL_TEAM_ID')
        self.base_url = "https://api.vercel.com"

    def get_recent_deployments(self, project_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent deployments from Vercel"""
        if not self.api_token:
            logger.warning("Vercel API token not configured")
            return []

        url = f"{self.base_url}/v6/deployments"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {"limit": limit}

        if self.team_id:
            params["teamId"] = self.team_id
        if project_name:
            params["projectId"] = project_name

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            deployments = data.get("deployments", [])

            return [
                {
                    "id": d.get("uid"),
                    "name": d.get("name"),
                    "url": d.get("url"),
                    "state": d.get("state"),  # BUILDING, READY, ERROR, CANCELED
                    "created_at": d.get("createdAt"),
                    "ready_at": d.get("ready"),
                    "meta": d.get("meta", {})
                }
                for d in deployments
            ]

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Vercel deployments: {e}")
            return []

    def check_deployment_status(self, deployment_id: str) -> Optional[Dict]:
        """Check status of specific deployment"""
        if not self.api_token:
            return None

        url = f"{self.base_url}/v13/deployments/{deployment_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {}

        if self.team_id:
            params["teamId"] = self.team_id

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            deployment = response.json()

            return {
                "id": deployment.get("uid"),
                "name": deployment.get("name"),
                "url": deployment.get("url"),
                "state": deployment.get("readyState"),
                "created_at": deployment.get("createdAt"),
                "ready_at": deployment.get("ready"),
                "error": deployment.get("error"),
                "build_logs_url": deployment.get("inspectorUrl")
            }

        except requests.RequestException as e:
            logger.error(f"Failed to check deployment status: {e}")
            return None

    def detect_pr_deployment(self, branch_name: str, repo_name: Optional[str] = None) -> Optional[Dict]:
        """Detect if a deployment exists for a PR branch"""
        deployments = self.get_recent_deployments(repo_name, limit=20)

        for deployment in deployments:
            meta = deployment.get("meta", {})
            git_branch = meta.get("githubCommitRef") or meta.get("gitlabProjectName")

            if git_branch and git_branch == branch_name:
                return deployment

        return None

    def get_deployment_url(self, branch_name: str, repo_name: Optional[str] = None) -> Optional[str]:
        """Get deployment URL for a branch"""
        deployment = self.detect_pr_deployment(branch_name, repo_name)

        if deployment and deployment.get("state") == "READY":
            url = deployment.get("url")
            return f"https://{url}" if url and not url.startswith("http") else url

        return None

    def wait_for_deployment(self, deployment_id: str, timeout: int = 300) -> bool:
        """Wait for deployment to complete (blocking)"""
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.check_deployment_status(deployment_id)

            if not status:
                return False

            state = status.get("state")

            if state == "READY":
                logger.info(f"Deployment {deployment_id} completed successfully")
                return True
            elif state in ["ERROR", "CANCELED"]:
                logger.error(f"Deployment {deployment_id} failed with state: {state}")
                return False

            # Still building, wait
            time.sleep(10)

        logger.warning(f"Deployment {deployment_id} timed out after {timeout}s")
        return False

    def get_project_deployments(self, project_name: str) -> List[Dict]:
        """Get all deployments for a specific project"""
        if not self.api_token:
            return []

        url = f"{self.base_url}/v6/deployments"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {
            "projectId": project_name,
            "limit": 100
        }

        if self.team_id:
            params["teamId"] = self.team_id

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get("deployments", [])

        except requests.RequestException as e:
            logger.error(f"Failed to fetch project deployments: {e}")
            return []

    def is_configured(self) -> bool:
        """Check if Vercel integration is properly configured"""
        return bool(self.api_token)

    def test_connection(self) -> bool:
        """Test Vercel API connection"""
        if not self.api_token:
            logger.error("Vercel API token not configured")
            return False

        url = f"{self.base_url}/v6/deployments"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {"limit": 1}

        if self.team_id:
            params["teamId"] = self.team_id

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            logger.info("Vercel API connection successful")
            return True

        except requests.RequestException as e:
            logger.error(f"Vercel API connection failed: {e}")
            return False
