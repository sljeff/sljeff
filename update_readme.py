import os
import urllib.request


START_FLAG = "<!-- waka-box start -->"
END_FLAG = "<!-- waka-box end -->"

gist_id = os.environ.get("GIST_ID")
gh_user = os.environ.get("GH_USER")
readme_file = os.environ.get("README")


def main():
    content = urllib.request.urlopen(
        f"https://gist.githubusercontent.com/{gh_user}/{gist_id}/raw",
    ).read().decode()

    with open(readme_file) as f:
        readme = f.read()

    start = readme.find(START_FLAG)
    end = readme.find(END_FLAG)

    if start == -1 or end == -1:
        return

    before = readme[:start + len(START_FLAG)]
    after = readme[end:]

    result = [before]

    # title
    name = "📊 Weekly development breakdown"
    result.append(f'#### <a href="https://gist.github.com/{gist_id}" target="_blank">{name}</a>')

    # content
    result.append("```text")
    result.append(content)
    result.append("```")

    result.append(after)

    with open(readme_file, "w") as f:
        f.write("\n".join(result))


main()
