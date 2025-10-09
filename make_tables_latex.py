import re
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

def parse_strategy(strategy_str: str, normalize: bool = False, max_iterations: int = 1500) -> tuple:
    numbers = list(map(int, re.findall(r'np\.int64\((\d+)\)', strategy_str)))
    if normalize:
        return tuple(round(n / max_iterations, 2) for n in numbers)
    else:
        return tuple(numbers)

def determine_decimal_places(probabilities: List[float]) -> int:
    min_decimal_places = 2
    max_decimal_places = 8
    
    for decimal_places in range(min_decimal_places, max_decimal_places + 1):
        rounded_probs = [round(p, decimal_places) for p in probabilities]
        
        all_distinguishable = True
        for i, orig_prob in enumerate(probabilities):
            rounded_prob = rounded_probs[i]
            
            if orig_prob > 0 and rounded_prob == 0:
                all_distinguishable = False
                break
            
            for j, other_prob in enumerate(probabilities):
                if i != j and abs(orig_prob - other_prob) > 0:
                    if round(orig_prob, decimal_places) == round(other_prob, decimal_places):
                        if abs(orig_prob - other_prob) > 10**(-decimal_places-1):
                            all_distinguishable = False
                            break
            
            if not all_distinguishable:
                break
        
        if all_distinguishable:
            return decimal_places
    
    return max_decimal_places

def process_file(input_file: str, output_file: str, normalize: bool = False, max_iterations: int = 1500) -> None:
    with open(input_file, 'r') as f:
        lines = f.readlines()

    blocks = []
    current_block = []

    for line in lines:
        line = line.strip()
        if line == "-------------":
            if current_block:
                blocks.append(current_block)
                current_block = []
        elif line:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    with open(output_file, 'w') as f:
        f.write(r'\begin{tabular}{|c|c|c|}' + '\n')
        f.write(r'\hline' + '\n')
        f.write('Player & Pure Strategy & Probability \\\\ \n')
        f.write(r'\hline' + '\n')

        for i, block in enumerate(blocks):
            probabilities = []
            for entry in block:
                match = re.match(r'(Alice|Bob)\s+\[(.*?)\]\s+([\d\.eE+-]+)', entry)
                if match:
                    _, _, probability = match.groups()
                    probabilities.append(float(probability))
            
            decimal_places = determine_decimal_places(probabilities)
            
            for entry in block:
                match = re.match(r'(Alice|Bob)\s+\[(.*?)\]\s+([\d\.eE+-]+)', entry)
                if match:
                    player, strategy_str, probability = match.groups()
                    strategy = parse_strategy(strategy_str, normalize=normalize, max_iterations=max_iterations)
                    
                    if normalize:
                        strategy_latex = '(' + ', '.join(f"{x:.2f}" for x in strategy) + ')'
                    else:
                        strategy_latex = str(strategy)
                    
                    prob_formatted = f"{float(probability):.{decimal_places}f}"
                    
                    f.write(f'{player} & {strategy_latex} & {prob_formatted} \\\\ \n')
            
            if i < len(blocks) - 1:
                f.write(r'\hline\hline' + '\n')

        f.write(r'\hline' + '\n')
        f.write(r'\end{tabular}' + '\n')

def read_csv_data(csv_file: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_file)
        return df
    except FileNotFoundError:
        print(f"Error: File {csv_file} not found.")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def csv_to_latex_table(df: pd.DataFrame, output_file: str, 
                      columns: Optional[List[str]] = None,
                      caption: str = "",
                      label: str = "",
                      decimal_places: int = 6,
                      scientific_notation: bool = False) -> None:
    
    if df is None:
        print("Error: DataFrame is None")
        return
    
    if columns:
        available_cols = [col for col in columns if col in df.columns and col != 'threshold']
        if not available_cols:
            print(f"Error: None of the specified columns {columns} found in CSV")
            return
        df = df[available_cols]
    else:
        df = df.drop(columns=['threshold'], errors='ignore')
    
    formatted_df = df.copy()
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
            if col == 'beta':
                formatted_df[col] = df[col].round(2)
            elif col == 'stale_rate':
                formatted_df[col] = df[col].round(3)
            elif scientific_notation and df[col].dtype in ['float64', 'float32']:
                formatted_df[col] = df[col].apply(lambda x: f"{x:.{decimal_places}e}")
            elif df[col].dtype in ['float64', 'float32']:
                formatted_df[col] = df[col].round(decimal_places)
    
    with open(output_file, 'w') as f:
        num_cols = len(formatted_df.columns)
        col_spec = '|' + 'c|' * num_cols
        f.write(f'\\begin{{tabular}}{{{col_spec}}}' + '\n')
        f.write(r'\hline' + '\n')
        
        headers = ' & '.join([col.replace('_', r'\_') for col in formatted_df.columns])
        f.write(headers + ' \\\\ \n')
        f.write(r'\hline' + '\n')
        
        for _, row in formatted_df.iterrows():
            row_str = ' & '.join([str(val) for val in row])
            f.write(row_str + ' \\\\ \n')
        
        f.write(r'\hline' + '\n')
        f.write(r'\end{tabular}' + '\n')

def csv_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    if df is None:
        return {}
    
    summary = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        summary[col] = {
            'mean': df[col].mean(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'median': df[col].median(),
            'count': df[col].count()
        }
    
    return summary

def filter_csv_data(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    if df is None:
        return None
    
    filtered_df = df.copy()
    
    for col, condition in filters.items():
        if col not in df.columns:
            print(f"Warning: Column '{col}' not found in DataFrame")
            continue
            
        if isinstance(condition, dict):
            if 'min' in condition:
                filtered_df = filtered_df[filtered_df[col] >= condition['min']]
            if 'max' in condition:
                filtered_df = filtered_df[filtered_df[col] <= condition['max']]
            if 'equals' in condition:
                filtered_df = filtered_df[filtered_df[col] == condition['equals']]
        else:
            filtered_df = filtered_df[filtered_df[col] == condition]
    
    return filtered_df

def group_csv_data(df: pd.DataFrame, group_by: str, agg_func: str = 'mean') -> pd.DataFrame:
    if df is None or group_by not in df.columns:
        return None
    
    if agg_func == 'mean':
        return df.groupby(group_by).mean().reset_index()
    elif agg_func == 'sum':
        return df.groupby(group_by).sum().reset_index()
    elif agg_func == 'count':
        return df.groupby(group_by).count().reset_index()
    elif agg_func == 'std':
        return df.groupby(group_by).std().reset_index()
    else:
        return df.groupby(group_by).agg(agg_func).reset_index()

def pivot_csv_data(df: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    if df is None:
        return None
    
    try:
        pivot_df = df.pivot_table(index=index, columns=columns, values=values, aggfunc='mean')
        return pivot_df.reset_index()
    except Exception as e:
        print(f"Error creating pivot table: {e}")
        return None

def csv_to_markdown_table(df: pd.DataFrame, output_file: str,
                         columns: Optional[List[str]] = None,
                         decimal_places: int = 4) -> None:
    if df is None:
        print("Error: DataFrame is None")
        return
    
    if columns:
        available_cols = [col for col in columns if col in df.columns]
        if not available_cols:
            print(f"Error: None of the specified columns {columns} found in CSV")
            return
        df = df[available_cols]
    
    formatted_df = df.copy()
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32']:
            formatted_df[col] = df[col].round(decimal_places)
    
    with open(output_file, 'w') as f:
        headers = '| ' + ' | '.join(formatted_df.columns) + ' |'
        f.write(headers + '\n')
        
        separator = '|' + '---|' * len(formatted_df.columns)
        f.write(separator + '\n')
        
        for _, row in formatted_df.iterrows():
            row_str = '| ' + ' | '.join([str(val) for val in row]) + ' |'
            f.write(row_str + '\n')

def create_comparison_table(df: pd.DataFrame, group_col: str, value_cols: List[str], 
                          output_file: str, format_type: str = 'latex') -> None:
    if df is None:
        return
    
    grouped = df.groupby(group_col)[value_cols].agg(['mean', 'std', 'min', 'max'])
    
    grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
    grouped = grouped.reset_index()
    
    if format_type == 'latex':
        csv_to_latex_table(grouped, output_file, 
                          caption=f"Comparison Table by {group_col}",
                          label=f"tab:comparison_{group_col}")
    elif format_type == 'markdown':
        csv_to_markdown_table(grouped, output_file)

def check_probability_sums(input_file: str) -> None:
    with open(input_file, 'r') as f:
        lines = f.readlines()

    blocks = []
    current_block = []

    for line in lines:
        line = line.strip()
        if line == "-------------":
            if current_block:
                blocks.append(current_block)
                current_block = []
        elif line:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    for i, block in enumerate(blocks):
        sums = {'Alice': 0.0, 'Bob': 0.0}
        for line in block:
            match = re.match(r'(Alice|Bob)\s+\[.*?\]\s+([\d\.eE+-]+)', line)
            if match:
                player, prob = match.groups()
                sums[player] += float(prob)
        print(f"Equilibrium {i+1}: Alice = {sums['Alice']:.12f}, Bob = {sums['Bob']:.12f}")

def analyze_csv_correlations(df: pd.DataFrame, output_file: str = None) -> pd.DataFrame:
    if df is None:
        return None
    
    numeric_df = df.select_dtypes(include=[np.number])
    correlation_matrix = numeric_df.corr()
    
    if output_file:
        csv_to_latex_table(correlation_matrix.round(4), output_file,
                          caption="Correlation Matrix", 
                          label="tab:correlations")
    
    return correlation_matrix

def export_filtered_data(df: pd.DataFrame, filters: Dict[str, Any], 
                        output_file: str, format_type: str = 'csv') -> None:
    filtered_df = filter_csv_data(df, filters)
    
    if filtered_df is None or filtered_df.empty:
        print("No data matches the filter criteria")
        return
    
    if format_type == 'csv':
        filtered_df.to_csv(output_file, index=False)
    elif format_type == 'latex':
        csv_to_latex_table(filtered_df, output_file)
    elif format_type == 'markdown':
        csv_to_markdown_table(filtered_df, output_file)
    
    print(f"Exported {len(filtered_df)} rows to {output_file}")
 

if __name__ == "__main__": 
    #max_iterations = 1500
    max_iterations = 8571866
    process_file('output.txt', 'output_latex.tex', normalize=False, max_iterations = max_iterations)
    check_probability_sums('output.txt')