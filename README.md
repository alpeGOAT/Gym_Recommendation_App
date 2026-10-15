
# Gym Recommendation App

A Python desktop application that recommends exercises using **Apriori association rule mining**. Select one exercise, and the app finds other exercises that frequently appear alongside it in recorded workouts.

The project combines data preprocessing with pandas, rule mining with mlxtend, and a Tkinter interface. A Windows executable can be built with PyInstaller.

[Download Windows releases](https://github.com/alpeGOAT/Gym_Recommendation_App/releases/latest) · [Source code](https://github.com/alpeGOAT/Gym_Recommendation_App)

> Recommendations describe patterns in the dataset. They are not personalized training plans or evidence that an exercise is appropriate for a particular person.

## Features

- Search exercise names without case sensitivity.
- Ignore leading, trailing, and repeated spaces in searches.
- Select a single exercise from the filtered list.
- Display up to five recommended exercises.
- Inspect support, confidence, and lift scores.
- Rank recommendations by lift, then confidence, then support.
- Clear the search, selection, and results.
- Show messages when no exercise is selected or no recommendation is available.
- Load data and generate rules in a background thread to keep the interface responsive.
- Run locally without a database, account, or network connection during normal operation.

## Download and run on Windows

1. Open the [Releases page](https://github.com/alpeGOAT/Gym_Recommendation_App/releases).
2. Select a release containing the application.
3. Under **Assets**, download **GymRecommendation.exe**.
4. Double-click the downloaded file.

The packaged executable includes the CSV dataset and required runtime dependencies. Python and PyCharm are not required to run that build.

Startup may take a little time: the single-file application unpacks its bundled files, then loads the dataset and generates association rules.

If a release has not been published yet, use the source-code instructions below.

## Run from source

### Requirements

- Python with Tkinter support.
- pandas.
- mlxtend.

PyCharm is optional. The source application uses a graphical desktop environment.

### 1. Clone the repository

```bash
git clone https://github.com/alpeGOAT/Gym_Recommendation_App.git
cd Gym_Recommendation_App
```

### 2. Create and activate a virtual environment

On Windows, using Command Prompt or the PyCharm terminal configured for Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

For Git Bash, activate it with:

```bash
source .venv/Scripts/activate
```

You can also use the existing project interpreter in PyCharm.

### 3. Install the application dependencies

```bash
python -m pip install pandas mlxtend
```

Tkinter is part of the Python standard library, but its availability depends on the Python installation. If importing it fails, install or enable Tk support for your Python distribution.

These commands provide a basic setup; they do not pin dependency versions. The repository also contains `pyproject.toml` and `uv.lock` for its project environment.

### 4. Check the dataset location

Keep the following file beside `gui.py`:

```text
weightlifting_721_workouts.csv
```

### 5. Launch the interface

```bash
python gui.py
```

To use the terminal-based recommendation flow instead:

```bash
python main.py
```

## How to use the application

1. Wait for the status message to indicate that loading has finished.
2. Enter part of an exercise name in the search field.
3. Select one exercise from the list.
4. Click **Öneri Getir** to display recommendations.
5. Click **Temizle** to reset the interface.

Double-clicking an exercise or pressing Enter while the exercise list has focus also requests recommendations.

Search is case-insensitive. For example, `lat`, `LAT`, and `Lat` produce the same filtered list. Partial matching helps find names such as `Leg Press (Machine)`, but recommendations use the selected exercise's actual name.

Some interface controls and status messages are in Turkish.

## How the recommendation system works

### 1. Clean the dataset

The preprocessing function:

- Removes `Notes` and `Workout Notes`, when present.
- Drops records missing `Date`, `Workout Name`, or `Exercise Name`.
- Trims leading and trailing whitespace in those fields.
- Removes records where a required field is empty after trimming.

### 2. Build workout transactions

Rows are grouped by **Date and Workout Name**. Each group becomes a list of unique exercises.

For example:

```python
["Lat Pulldown", "Chin Up", "Rear delt fly"]
```

Repeated sets of the same exercise count as one occurrence within that workout. Weights, repetitions, and exercise order do not affect the association rules.

This grouping assumes that the Date and Workout Name combination identifies a workout session in this dataset.

### 3. Encode transactions

`TransactionEncoder` converts the exercise lists into a Boolean table:

- Each row represents a workout.
- Each column represents an exercise.
- `True` indicates that the exercise appears in the workout.

### 4. Find frequent itemsets

Apriori uses these settings:

| Parameter | Value | Meaning |
|---|---:|---|
| Minimum support | 0.02 | An itemset must occur in at least 2% of workouts. |
| Maximum itemset length | 2 | Find single exercises and exercise pairs. |

### 5. Generate association rules

Rules require a minimum confidence of **0.20**, or **20%**.

Only rules with one exercise on each side are retained:

```text
Selected exercise → Recommended exercise
```

The first version accepts one selected exercise. It does not generate recommendations conditioned on multiple selected exercises.

### 6. Select and rank recommendations

The application matches the selected exercise to the rule antecedent, excludes the selected exercise itself, removes duplicate recommendation names, and returns at most five results.

Ordering is:

1. Lift, descending.
2. Confidence, descending.
3. Support, descending.

Exercise variations remain eligible recommendations. For example, selecting Bench Press does not automatically exclude Incline Bench Press.

There is no additional filter requiring lift to be above 1.

## Understanding the scores

Let **A** be the selected exercise and **B** be a recommended exercise.

| Metric | Calculation | Interpretation |
|---|---|---|
| Support | Workouts containing both A and B / All workouts | How common the pair is across the dataset. |
| Confidence | Workouts containing both A and B / Workouts containing A | How often B appears when A appears. |
| Lift | Confidence(A → B) / Support(B) | How common B is in workouts containing A compared with its overall frequency. |

In the interface, support and confidence are displayed as percentages. Lift is a ratio.

- **Lift > 1:** Positive association.
- **Lift = 1:** No association under this measure.
- **Lift < 1:** Negative association.

A confidence of 100% means every recorded workout containing A also contains B. It does not guarantee suitability or performance benefits.

### Example output

An observed result for **Lat Pulldown** was:

| Recommended exercise | Support | Confidence | Lift |
|---|---:|---:|---:|
| Rear delt fly | 3.6% | 56.8% | 4.796 |
| Chin Up | 6.3% | 100.0% | 3.005 |
| Bicep Curl (Barbell) | 2.6% | 40.5% | 2.717 |
| Hammer seated row (CLOSE GRIP) | 2.2% | 35.1% | 2.220 |

Values are rounded. Results depend on the dataset and thresholds. Rear delt fly ranks above Chin Up because lift takes priority over confidence.

## Project files

| File | Purpose |
|---|---|
| `main.py` | Data preparation, rule generation, recommendation function, and terminal entry point. |
| `gui.py` | Tkinter interface, background loading, search, and results table. |
| `weightlifting_721_workouts.csv` | Workout records used to generate recommendations. |
| `pyproject.toml` | Python project configuration. |
| `uv.lock` | Dependency lockfile for the uv project environment. |
| `.gitignore` | Excludes local environments and other generated files from Git. |
| `GymRecommendation.spec` | PyInstaller build configuration, generated during packaging. |

Packaging also creates `build/` and `dist/`. The executable is placed in `dist/`; these generated directories do not need to be committed.

## Build the Windows executable

Run the build on Windows using the Python environment where the source application works.

Install PyInstaller:

```bash
python -m pip install --upgrade pyinstaller
```

From the project directory:

```bash
python -m PyInstaller --onefile --windowed --name GymRecommendation --add-data "weightlifting_721_workouts.csv:." gui.py
```

The output is:

```text
dist/GymRecommendation.exe
```

- `--onefile` bundles the application into one executable.
- `--windowed` prevents a console window from opening.
- `--add-data` includes the dataset.

The application locates the CSV relative to `__file__`, allowing the same loading code to work with the bundled dataset.

Test the executable by opening it and requesting recommendations before uploading it to a release. The `.spec` file is not required by users running the executable.

## Troubleshooting

| Issue | What to check |
|---|---|
| Exercise is not visible | Search part of its name and select the exact dataset entry from the list. |
| No recommendations appear | The exercise may have no eligible rules under the current thresholds. |
| Fewer than five results appear | Five is a maximum; fewer qualifying rules produce fewer results. |
| CSV cannot be found | For source execution, place it beside `gui.py`. For the executable, rebuild with the provided `--add-data` option. |
| A Python module is missing | Install dependencies in the same interpreter used to run the app. |
| The executable fails without useful details | Rebuild without `--windowed` and run the new executable from a terminal to inspect errors. |

## Scope and limitations

- Recommendations reflect co-occurrence, not a validated measure of training quality.
- No user goals, experience, injuries, equipment availability, or recovery information are considered.
- Sets, repetitions, load, and exercise sequence are not used.
- Exercise naming and workout grouping affect the resulting rules.
- No standardized recommendation-quality evaluation has been performed.
- Rules are recalculated when the application starts.
- Updates are manual: changing the source or pushing to GitHub does not update an already downloaded executable.

The first version was manually checked for case-insensitive search, exercise selection, recommendation display, selection validation, and clearing the interface. The Windows executable was also created and placed on the developer's desktop.

## Dataset attribution

Dataset file: `weightlifting_721_workouts.csv`.

**Attribution to complete before publishing this README:**

- Original dataset page: add the source URL.
- Dataset creator: add the original author or publisher.
- Dataset license: add the exact license and any required attribution.

The dataset's license is separate from the application code's license. Public availability alone does not establish redistribution permissions.

## Code license

Consult a `LICENSE` file in the repository, if one is provided. This README does not assign a license to the project.

## Author

**Alperen Aydınlık**  
GitHub: [alpeGOAT](https://github.com/alpeGOAT)

