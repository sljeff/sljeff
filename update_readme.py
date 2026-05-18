import base64
import json
import os
import urllib.request


START_FLAG = "<!-- waka-box start -->"
END_FLAG = "<!-- waka-box end -->"
WAKATIME_STATS_URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"


def trim_right(value, width):
    return value if len(value) <= width else value[: width - 3] + "..."


def generate_bar_chart(percent, size=21):
    symbols = "░▏▎▍▌▋▊▉█"
    fraction = int(size * 8 * percent / 100)
    full_blocks = fraction // 8
    if full_blocks >= size:
        return symbols[-1] * size
    partial = fraction % 8
    return (symbols[-1] * full_blocks + symbols[partial]).ljust(size, symbols[0])


def build_wakatime_section(stats):
    languages = stats.get("data", {}).get("languages")
    if not isinstance(languages, list):
        raise ValueError("WakaTime response missing data.languages")

    lines = []
    for language in languages[:5]:
        name = trim_right(str(language.get("name", "Unknown")), 10).ljust(10)
        time = str(language.get("text", "0 secs")).ljust(14)
        percent = float(language.get("percent", 0))
        lines.append(
            " ".join(
                [
                    name,
                    time,
                    generate_bar_chart(percent),
                    f"{percent:.1f}%".rjust(6),
                ]
            )
        )

    content = "\n".join(lines) if lines else "No WakaTime data for the last 7 days."
    return "\n".join(
        [
            "#### 📊 Weekly development breakdown",
            "```text",
            content,
            "```",
        ]
    )


def replace_wakatime_section(readme, section):
    start = readme.find(START_FLAG)
    end = readme.find(END_FLAG)
    if start == -1 or end == -1 or end < start:
        raise ValueError("README missing waka-box markers")

    before = readme[: start + len(START_FLAG)]
    after = readme[end:]
    return "\n".join([before, section, after])


def fetch_wakatime_stats(api_key):
    if not api_key:
        raise ValueError("WAKATIME_API_KEY is required")

    token = base64.b64encode(api_key.encode()).decode()
    request = urllib.request.Request(
        WAKATIME_STATS_URL,
        headers={"Authorization": f"Basic {token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def main():
    readme_file = os.environ.get("README", "README.md")
    stats = fetch_wakatime_stats(os.environ.get("WAKATIME_API_KEY"))
    section = build_wakatime_section(stats)

    with open(readme_file) as f:
        readme = f.read()

    with open(readme_file, "w") as f:
        f.write(replace_wakatime_section(readme, section))


if __name__ == "__main__":
    main()
