"""Helper script to push the DocIQ repository to GitHub using a Personal Access Token."""

import sys
import dulwich.porcelain as porcelain

def main():
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
    else:
        print("GitHub requires a Personal Access Token (classic or fine-grained with 'repo' / 'contents:write' scope).")
        token = input("Enter your GitHub Personal Access Token (e.g. ghp_...): ").strip()

    if not token:
        print("Error: No token provided.")
        sys.exit(1)

    remote_url = f"https://itzbharathkumar0409:{token}@github.com/itzbharathkumar0409/technical-_document_-intelligence.git"

    print("Pushing 'main' branch to https://github.com/itzbharathkumar0409/technical-_document_-intelligence ...")
    try:
        porcelain.push(".", remote_url, "refs/heads/main:refs/heads/main")
        print("\nSUCCESS! All commits pushed to GitHub successfully.")
    except Exception as e:
        print(f"\nPush failed: {e}")
        print("Please ensure your token has write access to the repository.")

if __name__ == "__main__":
    main()
