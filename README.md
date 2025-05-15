# RL-CACHE: Accelerating PSQL Queries with Reinforcement Learning

This project demonstrates the use of a multi-level cache system to accelerate PostgreSQL queries using reinforcement learning. The system is built using PostgreSQL, Redis, Flask, and reinforcement learning algorithms.

## Prerequisites

- **PostgreSQL**: Ensure you have access to a PostgreSQL database. Supabase is recommended for online databases.
- **Redis**: Make sure the Redis server is running. You can use WSL (Windows Subsystem for Linux) to run Redis on Windows.
- **Python**: Ensure Python is installed on your system.
- **Flask**: Install Flask for running the web application.
- **Redis-py**: Install the Redis client for Python.
- **psycopg2**: Install the PostgreSQL adapter for Python.

## Setup Instructions

### Step 1: Create PostgreSQL Tables

1. **Access your PostgreSQL database** (e.g., Supabase).
2. **Run the SQL script** in `psql_database_creation.txt` to create the necessary tables. This script includes the creation of tables such as `users`, `products`, `orders`, etc.

### Step 2: Generate and Upload CSV Data

1. **Run `generate.py`** to generate CSV files for users, products, orders, reviews, seasons, and promotions.
   ```bash
   python generate.py
   ```
2. **Upload the generated CSV files** to the corresponding tables in your PostgreSQL database. This can typically be done through the database's import functionality.

### Step 3: Set Up the Application

1. **Ensure `redis_rl_cache_simulation.py`, `index.html`, and `app.py`** are in the same directory.
2. **Start the Redis server**. If using WSL, you can start Redis with:
   ```bash
   redis-server
   ```

### Step 4: Run the Flask Application

1. **Start the Flask application** by running `app.py`:
   ```bash
   python app.py
   ```
2. **Open your web browser** and navigate to `http://localhost:5000` to view the simulation dashboard.

### Step 5: View the Simulation

- The HTML page will display the live simulation results, showing the performance improvements with and without caching by sending them live on two seperate threads so you can see realtime how much my rl based caching increases the speed with so little resources.
- ![image](https://github.com/user-attachments/assets/e529a53d-cbaa-4cc0-a8bd-dca7aad1ba78)


## Additional Information

- **Redis Configuration**: Ensure Redis is configured to allow sufficient memory for caching.
- **Database Connection**: Update the database connection details in `redis_rl_cache_simulation.py` if necessary.
- **Simulation Parameters**: You can adjust the simulation parameters in `redis_rl_cache_simulation.py` to test different scenarios.

## License

Copyright © 2025  
All rights reserved. Maddi Rishi Dhaneswar

This software and its associated documentation are proprietary and confidential.  
Unauthorized use, reproduction, distribution, or modification of any part of this codebase is strictly prohibited without explicit written permission from the owner (Maddi Rishi Dhaneswar).

This repository is shared for academic evaluation and publication purposes only.

If you wish to collaborate, request access, or seek clarification, please contact:  
maddi.rishi2468@gmail.com

No license is granted by implication, estoppel, or otherwise.

