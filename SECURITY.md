# Security

HaoStory is designed to keep raw work evidence local. Do not publish a `.haostory/` directory without reviewing its privacy report and every selected asset.

Report a vulnerability privately through the contact channel at <https://howie.wang/>. Do not include real credentials, private source code, or personal data in a public issue.

Before publishing an example:

1. Run `python3 skill/haostory/scripts/haostory.py audit <session>`.
2. Review `privacy-report.json` and all copied images manually.
3. Search the repository and Git history for secrets and absolute paths.
4. Rotate any credential that may have been exposed, even if it was later deleted.

