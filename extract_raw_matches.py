import re

log_file_path = "/mnt/e/source/personal_repos/homeassistant/docker/config/home-assistant.log"
output_file_path = "/mnt/e/source/personal_repos/homeassistant/custom_components/price_tracker/raw_matches.txt"

with open(log_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
    for line in infile:
        match = re.search(r'Raw self.__next_f.push\(\) match: (.*)', line)
        if match:
            outfile.write(match.group(1) + '\n')