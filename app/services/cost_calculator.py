# app/services/cost_calculator.py
import os
import tiktoken


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def count_tokens(text):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    return len(tokens)


def calculate_cost(tokens, rate_per_1k_tokens):
    return (tokens / 1000) * rate_per_1k_tokens


def append_cost_to_file(input_file, output_file, cost_file="0_cost_rupiah.txt"):
    if not os.path.isfile(input_file):
        print(f"File not found: {input_file}")
        return

    if not os.path.isfile(output_file):
        print(f"File not found: {output_file}")
        return

    prompt_input_text = read_file(input_file)
    prompt_output_text = read_file(output_file)

    prompt_input_token_count = count_tokens(prompt_input_text)
    prompt_output_token_count = count_tokens(prompt_output_text)

    total_token_count = prompt_input_token_count + prompt_output_token_count

    # Rates and conversion
    input_rate_per_1k_tokens = 0.005
    output_rate_per_1k_tokens = 0.015
    api_call_cost = 0.0080
    usd_to_idr = 16500

    input_cost_usd = calculate_cost(
        prompt_input_token_count, input_rate_per_1k_tokens)
    output_cost_usd = calculate_cost(
        prompt_output_token_count, output_rate_per_1k_tokens)
    total_cost_usd = input_cost_usd + output_cost_usd + api_call_cost

    input_cost_idr = input_cost_usd * usd_to_idr
    output_cost_idr = output_cost_usd * usd_to_idr
    total_cost_idr = total_cost_usd * usd_to_idr

    with open(cost_file, 'a', encoding='utf-8') as file:
        file.write(f"Input File: {input_file}\n")
        file.write(f"Output File: {output_file}\n")
        file.write(f"Input Token Count: {prompt_input_token_count}\n")
        file.write(f"Output Token Count: {prompt_output_token_count}\n")
        file.write(f"Total Token Count: {total_token_count}\n")
        file.write(f"Rp for Input: Rp {input_cost_idr:.2f}\n")
        file.write(f"Rp for Output: Rp {output_cost_idr:.2f}\n")
        file.write(
            f"Rp for Total (including API Call): Rp {total_cost_idr:.2f}\n")
        file.write("\n")
