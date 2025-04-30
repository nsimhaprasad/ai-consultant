#!/usr/bin/env python3

import subprocess
import argparse
import sys
import re


def parse_args():
    parser = argparse.ArgumentParser(description='Delete multiple Vertex AI agents')
    parser.add_argument('--project_id', required=True, help='Google Cloud project ID')
    parser.add_argument('--location', required=True, help='Google Cloud location')
    parser.add_argument('--bucket', required=True, help='Google Cloud Storage bucket')
    parser.add_argument('--dry_run', action='store_true', help='Print commands without executing them')
    parser.add_argument('--skip_confirmation', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--force', action='store_true', help='Force delete agents including all child resources')
    return parser.parse_args()


def get_agent_ids(project_id, location, bucket):
    """Dynamically get the list of agent IDs using the list command"""
    print(f"Retrieving current agents from Vertex AI...")

    command = [
        "python3", "deploy.py",
        "--list",
        "--project_id", project_id,
        "--location", location,
        "--bucket", bucket
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout.strip()

        # Extract agent IDs using regex
        agent_ids = []
        for line in output.split('\n'):
            if line.startswith('Agent: '):
                agent_id = line.replace('Agent: ', '').strip()
                agent_ids.append(agent_id)

        return agent_ids
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving agents: {e.stderr.strip()}")
        sys.exit(1)


def main():
    args = parse_args()

    # Dynamically get agent IDs
    agent_ids = get_agent_ids(args.project_id, args.location, args.bucket)

    if not agent_ids:
        print("No agents found to delete. Exiting.")
        return

    # Skip the first agent (latest one)
    agents_to_delete = agent_ids[1:]

    if not agents_to_delete:
        print("Only one agent found (the latest). Nothing to delete.")
        print(f"Preserved agent: {agent_ids[0]}")
        return

    print(f"Found {len(agent_ids)} total agents.")
    print(f"Preserving the latest agent: {agent_ids[0]}")
    print(f"Preparing to delete {len(agents_to_delete)} older agents:")

    for i, agent_id in enumerate(agents_to_delete, 1):
        print(f"  {i}. {agent_id}")

    # Confirmation prompt
    if not args.skip_confirmation and not args.dry_run:
        confirmation = input(f"\nAre you sure you want to delete these {len(agents_to_delete)} agents? (y/n): ")
        if confirmation.lower() not in ['y', 'yes']:
            print("Operation cancelled by user.")
            return

    success_count = 0
    failed_count = 0

    print(f"\nProceeding to delete {len(agents_to_delete)} agents...")

    for i, agent_id in enumerate(agents_to_delete, 1):
        print(f"\n[{i}/{len(agents_to_delete)}] Deleting agent: {agent_id}")

        command = [
            "python3", "deploy.py",
            "--delete",
            "--project_id", args.project_id,
            "--location", args.location,
            "--bucket", args.bucket,
            "--resource_id", agent_id
        ]

        # Add force_delete flag if specified
        if args.force:
            command.append("--force_delete")

        cmd_str = " ".join(command)
        print(f"Running: {cmd_str}")

        if args.dry_run:
            print("DRY RUN: Command not executed")
            continue

        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"Success: {result.stdout.strip() or 'Agent deleted'}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr.strip()}")
            failed_count += 1

    print(f"\nDeletion summary:")
    print(f"- Total agents found: {len(agent_ids)}")
    print(f"- Preserved latest agent: {agent_ids[0]}")
    print(f"- Agents selected for deletion: {len(agents_to_delete)}")
    print(f"- Successfully deleted: {success_count}")
    print(f"- Failed to delete: {failed_count}")


if __name__ == "__main__":
    main()