# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Deployment script for AI Consultant Agent."""

import os
import sys
import google.auth
import requests

# Ensure the script runs from the ai-consultant-agent root for correct packaging
os.chdir(os.path.dirname(os.path.dirname(__file__)))

# Ensure the parent directory is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from absl import app
from absl import flags
from dotenv import load_dotenv
from ai_consultant_agent.agent import root_agent
import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket.")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")

flags.DEFINE_bool("list", False, "List all agents.")
flags.DEFINE_bool("create", False, "Creates a new agent.")
flags.DEFINE_bool("delete", False, "Deletes an existing agent.")
flags.mark_bool_flags_as_mutual_exclusive(["create", "delete"])

_AI_PLATFORM_GIT = (
    "git+https://github.com/googleapis/python-aiplatform.git@copybara_738852226"
)

flags.DEFINE_bool("force_delete", False, "Force delete agent and all child resources.")


def create() -> None:
    """Creates an agent engine for AI Consultant Agent."""
    adk_app = AdkApp(agent=root_agent, enable_tracing=True)

    remote_agent = agent_engines.create(
        adk_app,
        display_name=root_agent.name,
        requirements=[
            "google-adk (>=0.4.0)",
            # f"google-cloud-aiplatform[agent_engines] @ {_AI_PLATFORM_GIT}",
            "google-genai (>=1.5.0,<2.0.0)",
            "pydantic (>=2.10.6,<3.0.0)",
            "absl-py (>=2.2.1,<3.0.0)",
            "anthropic[vertex] (>=0.18.0)",
            "python-dotenv (>=1.0.0)",
            "google-cloud-aiplatform (>=2.20.0)"
        ],
        extra_packages=["./ai_consultant_agent"],
    )
    resource_name = remote_agent.resource_name
    print(f"Created remote agent: {resource_name}")
    # Write resource_name to a file for server redeployment automation
    with open("agent_resource.txt", "w") as f:
        f.write(resource_name)


def delete(resource_id: str, location: str, force: bool = False) -> None:
    """Deletes an existing agent engine."""
    print(f"Deleting AgentEngine resource: {resource_id}")
    agent_engines.delete(resource_id, force=force)
    print(f"Deleted agent: {resource_id}")


def list_agents() -> None:
    """Lists all agent engines."""
    agents = agent_engines.list()
    for agent in agents:
        print(f"Agent: {agent.resource_name}")


def main(argv: list[str]):
    load_dotenv()
    project_id = FLAGS.project_id or os.getenv("PROJECT_ID")
    location = FLAGS.location or os.getenv("LOCATION")
    bucket = FLAGS.bucket or os.getenv("BUCKET")
    resource_id = FLAGS.resource_id or os.getenv("RESOURCE_ID")

    if not project_id or not location or not bucket:
        raise ValueError("project_id, location, and bucket are required.")

    vertexai.init(project=project_id, location=location, staging_bucket=bucket)

    if FLAGS.list:
        list_agents()
    elif FLAGS.create:
        create()
    elif FLAGS.delete:
        if not resource_id:
            raise ValueError("resource_id is required for deletion.")
        delete(resource_id, location, force=FLAGS.force_delete)
    else:
        print("No action specified. Use --list, --create, or --delete.")


if __name__ == "__main__":
    app.run(main)
