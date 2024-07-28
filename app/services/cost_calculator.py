# app/services/cost_calculator.py
def calculate_cost(input_token_count, output_token_count):
    input_rate_per_1k_tokens = 0.005
    output_rate_per_1k_tokens = 0.015
    api_call_cost = 0.0080
    usd_to_idr = 16500

    input_cost_usd = (input_token_count / 1000) * input_rate_per_1k_tokens
    output_cost_usd = (output_token_count / 1000) * output_rate_per_1k_tokens
    total_cost_usd = input_cost_usd + output_cost_usd + api_call_cost

    total_cost_idr = total_cost_usd * usd_to_idr
    return total_cost_idr
