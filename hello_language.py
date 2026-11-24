import os


def main():
    name = os.getenv("USERNAME")
    language = os.getenv("LANGUAGE")
    print(f"Hello, {name} from GitHub! Your favorite language is {language}.")


if __name__ == "__main__":
    main()
