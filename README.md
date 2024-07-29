# Locust Performance Testing

This repository contains performance tests written with [Locust](https://locust.io/). Locust is an open-source load testing tool for web applications.

## Prerequisites

Ensure you have the following installed:

- Python 3.6 or later
- `pip` (Python package installer)

## Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/hush-tukul/locust_test
    cd your-repo
    ```

2. Create and activate a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Running Locust

To run the Locust performance tests, use the following command:

```bash
locust -f locustfile.py
