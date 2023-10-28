import json
import time

import requests




def retry_on_error(func):
    def wrapper(*args, **kwargs):
        json_decode_delay = 20
        read_time_out_delay = 60
        retry_attempts = 1
        attempts = 0
        while attempts <= retry_attempts:
            try:
                return func(*args, **kwargs)

            except requests.exceptions.ReadTimeout:
                if attempts < retry_attempts:
                    print(f"Read Timeout encountered. Retrying attempt {attempts + 1} in {read_time_out_delay} seconds...")
                    time.sleep(read_time_out_delay)
                    attempts += 1

            except json.decoder.JSONDecodeError:
                if attempts < retry_attempts:
                    print(f"Json Decode encountered. Retrying attempt {attempts + 1} in {json_decode_delay} seconds...")
                    time.sleep(json_decode_delay)
                    attempts += 1
                else:
                    print(f"Max retry attempts reached. Failing after {retry_attempts} attempts.")
                    raise
    return wrapper
