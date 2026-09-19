from higgsfield_companion import generate, output_urls


def main() -> None:
    result = generate(
        "higgsfield-ai/soul/standard",
        {
            "prompt": "Editorial portrait in soft daylight",
            "num_images": 1,
            "resolution": "2K",
            "aspect_ratio": "4:3",
        },
    )
    for url in output_urls(result):
        print(url)


if __name__ == "__main__":
    main()
