__author__ = "akeshavan"
import glob
import json
import os
import posixpath
import shutil
from urllib.parse import urlsplit, urlunsplit

from jinja2 import Environment, FileSystemLoader


def relative_url(url, from_directory="."):
    """Resolve a site-relative URL from a generated file's directory."""
    parts = urlsplit(url)
    if not parts.path or parts.scheme or parts.netloc or parts.path.startswith("/"):
        return url

    path = posixpath.relpath(parts.path, start=from_directory)
    return urlunsplit(("", "", path, parts.query, parts.fragment))


def load_json(filename):
    """Load data from a json file"""
    with open(filename, "r") as fp:
        data = json.load(fp)
    return data


def load_projects(directory, github_repo):
    """
    Scans the 'data/projects' directory for JSON files,
    loads them, and adds a link to the original GitHub issue.
    """
    projects = []
    # Check if directory exists to avoid errors on fresh clones
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} not found. No projects loaded.")
        return projects

    # Glob all json files
    for filename in glob.glob(os.path.join(directory, "*.json")):
        try:
            data = load_json(filename)

            if "issue_number" in data:
                data["issue_url"] = (
                    f"https://github.com/{github_repo}/issues/{data['issue_number']}"
                )

            projects.append(data)
        except Exception as e:
            print(f"Skipping {filename}: {e}")

    # Optional: Sort projects by issue number (earliest first)
    projects.sort(key=lambda x: int(x.get("issue_number", 0)))
    return projects


files_to_generate = [
    {"filename": "index.html.j2", "location": "./_site"},
    {"filename": "projects.html.j2", "location": "./_site"},  # New projects page
    {"filename": "css/stylish-portfolio.css.j2", "location": "./_site"},
]

env = Environment(loader=FileSystemLoader("./_site"))
env.filters["relative_url"] = relative_url
info = load_json("data.json")

# GitHub Pages publishes only the generated ``_site`` directory. Copy static
# assets into it so relative URLs in data.json are included in the deployment.
shutil.copytree("assets", "_site/assets", dirs_exist_ok=True)

# Load the project data and add it to the 'info' dictionary
info["projects"] = load_projects("data/projects", info["github_repo"])

for f in files_to_generate:
    try:
        template = env.get_template(f["filename"])
        # Handle the output filename (remove .j2)
        outfile_name = f["filename"].replace(".j2", "")
        outfile = os.path.join(f["location"], outfile_name)

        print("writing", outfile)
        with open(outfile, "w", encoding="utf-8") as q:
            q.write(template.render(**info))
    except Exception as e:
        print(f"Error generating {f['filename']}: {e}")
