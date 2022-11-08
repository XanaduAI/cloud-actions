import os

def main():
    print(f"Using github event name {os.environ['GITHUB_EVENT_NAME']}")

if __name__ == "__main__":
    main()
