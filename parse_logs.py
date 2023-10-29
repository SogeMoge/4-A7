"""Functions for parsing log files generated bythe X-Wing Squadron Bot."""

import json
from collections import defaultdict

# Open the log file
with open("xwsbot.log", "r") as f:
    # Initialize counters
    info_counts = defaultdict(int)
    username_counts = defaultdict(int)

    # Loop over each line in the file
    for line in f:
        # Parse the JSON object
        log_dict = json.loads(line)

        # Check if the log level is INFO
        if log_dict["level"] == "INFO":
            # Increment the info count for the month
            month = log_dict["timestamp"][:7]
            if log_dict["username"] != "sogemoge":
                info_counts[month] += 1

        # Increment the username count (excluding "sogemoge")
        if log_dict["username"] != "sogemoge":
            if log_dict["level"] == "INFO":
                username_counts[log_dict["username"]] += 1

# Print the info counts by month
print("###### INFO counts by month:")
for month, count in info_counts.items():
    print(f"{month}: {count} INFO entries")

print("\n###### Event counts by user:")
# Print the username counts (excluding "sogemoge")
user_count = 0
for username, count in username_counts.items():
    user_count += 1
    print(f"{user_count}. {username}: {count} entries")
