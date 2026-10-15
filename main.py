import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

def normalize_name(name):
    return " ".join(str(name).split()).casefold()

def prepare_transactions(file_path):
    df = pd.read_csv(file_path)

    df = df.drop(columns=["Notes", "Workout Notes"], errors="ignore")
    required_columns = ["Date", "Workout Name", "Exercise Name"]
    df = df.dropna(subset=required_columns)

    for column in required_columns:
        df[column] = df[column].astype(str).str.strip()

    df = df[df[required_columns].ne("").all(axis=1)]

    basket = (
        df.groupby(["Date", "Workout Name"])["Exercise Name"]
        .apply(lambda exercises: sorted(set(exercises)))
    )

    return basket.tolist()


def create_rules(transactions, min_support=0.02, min_confidence=0.2):
    if not transactions:
        raise ValueError("No Records left after data cleaned.")

    encoder = TransactionEncoder()
    encoded_array = encoder.fit(transactions).transform(transactions)

    df_encoded = pd.DataFrame(
        encoded_array,
        columns=encoder.columns_
    )

    frequent_items = apriori(
        df_encoded,
        min_support=min_support,
        use_colnames=True,
        max_len=2
    )

    if not frequent_items["itemsets"].apply(len).eq(2).any():
        rules = pd.DataFrame(
            columns=[
                "antecedents",
                "consequents",
                "support",
                "confidence",
                "lift"
            ]
        )
    else:
        rules = association_rules(
            frequent_items,
            metric="confidence",
            min_threshold=min_confidence
        )

    rules = rules[
        rules["antecedents"].apply(len).eq(1)
        & rules["consequents"].apply(len).eq(1)
    ].copy()

    rules["antecedents_text"] = rules["antecedents"].apply(
        lambda items: next(iter(items))
    )
    rules["consequents_text"] = rules["consequents"].apply(
        lambda items: next(iter(items))
    )

    rules = rules.sort_values(
        by=["lift", "confidence", "support"],
        ascending=False
    ).reset_index(drop=True)

    return rules, sorted(encoder.columns_)


def get_exercise_recommendation(exercise_name, rules_df, top_n=5):
    result_columns = [
        "antecedents_text",
        "consequents_text",
        "support",
        "confidence",
        "lift"
    ]

    normalized_name = normalize_name(exercise_name)

    if not normalized_name or top_n <= 0:
        return pd.DataFrame(columns=result_columns)

    matched_rules = rules_df[
        rules_df["antecedents_text"].map(normalize_name).eq(normalized_name)
    ].copy()

    matched_rules = matched_rules[
        ~matched_rules["consequents_text"]
        .map(normalize_name)
        .eq(normalized_name)
    ]

    matched_rules = matched_rules.sort_values(
        by=["lift", "confidence", "support"],
        ascending=False
    )

    matched_rules = matched_rules.drop_duplicates(
        subset=["consequents_text"]
    )

    return matched_rules[result_columns].head(top_n).reset_index(drop=True)


def main():
    file_path = "weightlifting_721_workouts.csv"

    transactions = prepare_transactions(file_path)

    rules, exercise_names = create_rules(
        transactions,
        min_support=0.02,
        min_confidence=0.2
    )

    print(f"Total Workouts: {len(transactions)}")
    print(f"Total Exercises: {len(exercise_names)}")
    print(f"Total Rules: {len(rules)}")

    if rules.empty:
        print("No rules found with the current thresholds.")
        return

    exercise_name = input("\nEnter Exercise Name: ").strip()

    if not exercise_name:
        print("Please enter an exercise name.")
        return

    name_lookup = {
        normalize_name(name): name
        for name in exercise_names
    }

    normalized_input = normalize_name(exercise_name)

    if normalized_input not in name_lookup:
        similar_names = [
            name for name in exercise_names
            if normalized_input in normalize_name(name)
        ]

        print(f"Exercise not found: {exercise_name}")

        if similar_names:
            print("\nMatching exercise names in the dataset:")
            for name in similar_names:
                print(f"- {name}")
        else:
            print("No similar exercise names found.")

        return

    exercise_name = name_lookup[normalized_input]

    recommendations = get_exercise_recommendation(
        exercise_name,
        rules,
        top_n=5
    )

    if recommendations.empty:
        print(f"No recommendations found for: {exercise_name}")
        return

    print(f"\nRecommended Exercises Based On {exercise_name}")
    print(
        recommendations.to_string(
            index=False,
            float_format=lambda value: f"{value:.3f}"
        )
    )

if __name__ == "__main__":
    main()