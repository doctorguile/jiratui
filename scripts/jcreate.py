#!/usr/bin/env python3
"""
Create Jira tickets from the command line.

Usage:
    jcreate.py "Summary text" [-p PROJ|SRE] [-t task|bug] [-d "description"] [-f "fixVersion"] [-a assignee]

Examples:
    jcreate.py "Fix login bug" -t bug
    jcreate.py "Deploy service" -p SRE -a asmith
    jcreate.py "Add feature" -d "Detailed description" -f "v2026.2"
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# Configuration
JIRA_BASE_URL = os.environ.get('JIRA_BASE_URL', 'https://jira.example.com')
JIRA_TOKEN = os.environ.get('JIRA_TOKEN', '')

# Issue type and priority IDs
ISSUE_TYPES = {
    'task': '10100',
    'bug': '10102',
}
PRIORITY_P2 = '10301'

# Project defaults
PROJECT_DEFAULTS = {
    'PROJ': {
        'assignee': os.environ.get('USER', 'jdoe'),
        'supports_fix_version': True,
    },
    'SRE': {
        'assignee': 'jsmith',
        'supports_fix_version': False,
    },
}


def list_fix_versions(project: str, show_all: bool = False) -> list[dict]:
    """List available fix versions for a project."""

    if not JIRA_TOKEN:
        raise ValueError('JIRA_TOKEN environment variable is not set')

    project = project.upper()
    url = f'{JIRA_BASE_URL}/rest/api/2/project/{project}/versions'
    request = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {JIRA_TOKEN}'},
    )

    try:
        with urllib.request.urlopen(request) as response:
            versions = json.loads(response.read().decode('utf-8'))
            if not show_all:
                # Filter to unreleased, non-archived versions
                versions = [v for v in versions if not v.get('released') and not v.get('archived')]
            return versions
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f'Project not found: {project}')
        error_body = e.read().decode('utf-8')
        raise ValueError(f'Jira API error ({e.code}): {error_body}')


def create_issue(
    summary: str,
    project: str = 'PROJ',
    issue_type: str = 'task',
    description: str | None = None,
    fix_version: str | None = None,
    assignee: str | None = None,
) -> dict:
    """Create a Jira issue and return the response."""

    if not JIRA_TOKEN:
        raise ValueError('JIRA_TOKEN environment variable is not set')

    project = project.upper()
    if project not in PROJECT_DEFAULTS:
        raise ValueError(f'Unknown project: {project}. Supported: {", ".join(PROJECT_DEFAULTS.keys())}')

    issue_type = issue_type.lower()
    if issue_type not in ISSUE_TYPES:
        raise ValueError(f'Unknown issue type: {issue_type}. Supported: {", ".join(ISSUE_TYPES.keys())}')

    # Use project default assignee if not specified
    if assignee is None:
        assignee = PROJECT_DEFAULTS[project]['assignee']

    # Build the payload
    fields = {
        'project': {'key': project},
        'summary': summary,
        'issuetype': {'id': ISSUE_TYPES[issue_type]},
        'priority': {'id': PRIORITY_P2},
        'assignee': {'name': assignee},
    }

    if description:
        fields['description'] = description

    if fix_version:
        if not PROJECT_DEFAULTS[project]['supports_fix_version']:
            print(f'Warning: {project} does not support fixVersion, ignoring -f flag', file=sys.stderr)
        else:
            fields['fixVersions'] = [{'name': fix_version}]

    payload = json.dumps({'fields': fields}).encode('utf-8')

    # Make the request
    url = f'{JIRA_BASE_URL}/rest/api/2/issue'
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Authorization': f'Bearer {JIRA_TOKEN}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_json = json.loads(error_body)
            raise ValueError(f'Jira API error: {json.dumps(error_json, indent=2)}')
        except json.JSONDecodeError:
            raise ValueError(f'Jira API error ({e.code}): {error_body}')


def main():
    parser = argparse.ArgumentParser(
        description='Create Jira tickets from the command line.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s "Fix login bug" -t bug
  %(prog)s "Deploy service" -p SRE -a asmith
  %(prog)s "Add feature" -d "Detailed description" -f "v2026.2"
  %(prog)s -l                    # List available fix versions for PROJ
  %(prog)s -l -p PROJ --all       # List all versions (including released/archived)

Environment variables:
  JIRA_BASE_URL  Jira server URL (default: https://jira.example.com)
  JIRA_TOKEN     Bearer token for authentication (required)
''',
    )

    parser.add_argument(
        'summary',
        nargs='?',  # Optional when using -l
        help='Issue summary/title (required unless using -l)',
    )
    parser.add_argument(
        '-p', '--project',
        default='PROJ',
        choices=['PROJ', 'SRE', 'drs', 'sreas'],
        help='Project key (default: PROJ)',
    )
    parser.add_argument(
        '-t', '--type',
        default='task',
        choices=['task', 'bug'],
        help='Issue type (default: task)',
    )
    parser.add_argument(
        '-d', '--description',
        help='Issue description',
    )
    parser.add_argument(
        '-f', '--fix-version',
        help='Fix version (PROJ only, e.g., v2026.2)',
    )
    parser.add_argument(
        '-a', '--assignee',
        help='Assignee username (default: jdoe for PROJ, jsmith for SRE)',
    )
    parser.add_argument(
        '-l', '--list-fix-versions',
        action='store_true',
        help='List available fix versions for the project',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='With -l: include released and archived versions',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print the payload without creating the issue',
    )

    args = parser.parse_args()

    # Handle -l / --list-fix-versions
    if args.list_fix_versions:
        try:
            versions = list_fix_versions(args.project, show_all=args.all)
            if not versions:
                print(f'No {"" if args.all else "unreleased "}versions found for {args.project.upper()}')
                return
            print(f'Fix versions for {args.project.upper()}:')
            for v in versions:
                status = []
                if v.get('released'):
                    status.append('released')
                if v.get('archived'):
                    status.append('archived')
                status_str = f' ({", ".join(status)})' if status else ''
                print(f'  {v["name"]}{status_str}')
        except ValueError as e:
            print(f'Error: {e}', file=sys.stderr)
            sys.exit(1)
        return

    # Summary is required for creating issues
    if not args.summary:
        parser.error('summary is required (or use -l to list fix versions)')

    if args.dry_run:
        project = args.project.upper()
        assignee = args.assignee or PROJECT_DEFAULTS.get(project, {}).get('assignee', 'unknown')
        payload = {
            'fields': {
                'project': {'key': project},
                'summary': args.summary,
                'issuetype': {'id': ISSUE_TYPES[args.type]},
                'priority': {'id': PRIORITY_P2},
                'assignee': {'name': assignee},
            }
        }
        if args.description:
            payload['fields']['description'] = args.description
        if args.fix_version and PROJECT_DEFAULTS.get(project, {}).get('supports_fix_version'):
            payload['fields']['fixVersions'] = [{'name': args.fix_version}]
        print(json.dumps(payload, indent=2))
        return

    try:
        result = create_issue(
            summary=args.summary,
            project=args.project,
            issue_type=args.type,
            description=args.description,
            fix_version=args.fix_version,
            assignee=args.assignee,
        )

        key = result.get('key')
        if key:
            print(f'Created: {key}')
            print(f'{JIRA_BASE_URL}/browse/{key}')
        else:
            print(f'Unexpected response: {json.dumps(result, indent=2)}', file=sys.stderr)
            sys.exit(1)

    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f'Network error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
