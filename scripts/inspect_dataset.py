import argparse
import ast
import pandas as pd


def parse_list_column(value):
    if isinstance(value, list):
        return value

    if not isinstance(value, str):
        return value

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Path to pii_dataset.csv"
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    print("INSPECT DATASET")
    print("=" * 60)

    print(f"\n1. Số dòng dữ liệu: {len(df)}")
    print(f"2. Số cột: {len(df.columns)}")

    print("\n3. Danh sách cột:")
    for column in df.columns:
        print(f"- {column}")

    print("\n4. Một vài sample đầu tiên:")
    print(df.head())

    print("\n5. Kiểu dữ liệu của cột tokens và labels:")

    if "tokens" in df.columns:
        raw_tokens = df.loc[0, "tokens"]
        parsed_tokens = parse_list_column(raw_tokens)

        print(f"- tokens trước khi parse: {type(raw_tokens)}")
        print(f"- tokens sau khi parse: {type(parsed_tokens)}")

        if isinstance(parsed_tokens, list):
            print(f"- sample tokens: {parsed_tokens[:20]}")

    if "labels" in df.columns:
        raw_labels = df.loc[0, "labels"]
        parsed_labels = parse_list_column(raw_labels)

        print(f"- labels trước khi parse: {type(raw_labels)}")
        print(f"- labels sau khi parse: {type(parsed_labels)}")

        if isinstance(parsed_labels, list):
            print(f"- sample labels: {parsed_labels[:20]}")

    print("\n6. Danh sách nhãn BIO và số lượng từng loại nhãn:")

    label_counts = {}

    if "labels" in df.columns:
        for raw_labels in df["labels"]:
            labels = parse_list_column(raw_labels)

            if isinstance(labels, list):
                for label in labels:
                    label_counts[label] = label_counts.get(label, 0) + 1

    for label, count in sorted(label_counts.items()):
        print(f"- {label}: {count}")


if __name__ == "__main__":
    main()